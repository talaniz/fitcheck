"""Tests for fitcheck main module."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import main


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_config():
    return {
        "role": "Software Engineer",
        "experience": "5",
        "skills": ["Python", "Django", "PostgreSQL", "Docker", "Git"],
        "location": "San Francisco, CA",
        "location_preference": "Remote",
        "relocation": "no",
        "jobs_dir": "~/fitcheck/jobs",
        "industries": ["Tech", "Finance"],
        "must_haves": ["Remote work", "Equity"],
        "deal_breakers": ["On-site only", "No benefits"],
    }


@pytest.fixture
def minimal_config():
    """Config with optional fields empty (industries, must_haves, deal_breakers)."""
    return {
        "role": "Software Engineer",
        "experience": "5",
        "skills": ["Python", "Django", "PostgreSQL", "Docker", "Git"],
        "location": "San Francisco, CA",
        "location_preference": "Remote",
        "relocation": "no",
        "jobs_dir": "~/fitcheck/jobs",
        "industries": [],
        "must_haves": [],
        "deal_breakers": [],
    }


JOB_DESCRIPTION = "We are looking for a Senior Software Engineer at Acme Corp."

DEFAULT_RISK_INPUTS = {
    "days_posted": 7,
    "repost": "no",
    "has_timeline": True,
    "market_research": False,
    "role_disappeared": False,
}

DEFAULT_JD_QUALITY = {
    "problem_specificity": 3,
    "team_context": 2,
    "urgency_signal": 1,
    "reasoning": "Reasonably specific posting with some team context.",
}


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_ollama_response(filename, fit_score, assessment):
    """Build a mock ollama fit assessment response object."""
    content = json.dumps({
        "filename": filename,
        "fit_score": fit_score,
        "assessment": assessment,
    })
    response = MagicMock()
    response.message.content = content
    return response


def make_jd_quality_response(problem_specificity=3, team_context=2, urgency_signal=1,
                              reasoning="Reasonably specific posting."):
    """Build a mock ollama JD quality response object."""
    content = json.dumps({
        "problem_specificity": problem_specificity,
        "team_context": team_context,
        "urgency_signal": urgency_signal,
        "reasoning": reasoning,
    })
    response = MagicMock()
    response.message.content = content
    return response


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    def test_all_fields_populated(self, full_config):
        prompt = main.build_prompt(full_config, JOB_DESCRIPTION)

        assert "Software Engineer" in prompt
        assert "5" in prompt
        assert "Python, Django, PostgreSQL, Docker, Git" in prompt
        assert "San Francisco, CA" in prompt
        assert "Remote" in prompt
        assert "no" in prompt
        assert "Tech, Finance" in prompt
        assert "Remote work, Equity" in prompt
        assert "On-site only, No benefits" in prompt
        assert JOB_DESCRIPTION in prompt

    def test_optional_fields_absent_when_empty(self, minimal_config):
        prompt = main.build_prompt(minimal_config, JOB_DESCRIPTION)

        assert "Industries of interest" not in prompt
        assert "Must-haves" not in prompt
        assert "Deal breakers" not in prompt

    def test_required_fields_always_present(self, minimal_config):
        prompt = main.build_prompt(minimal_config, JOB_DESCRIPTION)

        assert "Role seeking" in prompt
        assert "Experience" in prompt
        assert "Skills" in prompt
        assert "Location" in prompt
        assert "Work preference" in prompt
        assert "Open to relocation" in prompt

    def test_prompt_contains_json_instruction(self, full_config):
        prompt = main.build_prompt(full_config, JOB_DESCRIPTION)

        assert "filename" in prompt
        assert "fit_score" in prompt
        assert "assessment" in prompt

    def test_job_description_included(self, full_config):
        job = "A unique job description string XYZ123"
        prompt = main.build_prompt(full_config, job)
        assert job in prompt


# ---------------------------------------------------------------------------
# build_jd_quality_prompt
# ---------------------------------------------------------------------------

class TestBuildJdQualityPrompt:
    def test_job_description_included(self):
        job = "Unique job description ABC456"
        prompt = main.build_jd_quality_prompt(job)
        assert job in prompt

    def test_prompt_contains_all_score_fields(self):
        prompt = main.build_jd_quality_prompt(JOB_DESCRIPTION)
        assert "problem_specificity" in prompt
        assert "team_context" in prompt
        assert "urgency_signal" in prompt
        assert "reasoning" in prompt

    def test_prompt_describes_higher_score_as_vaguer(self):
        prompt = main.build_jd_quality_prompt(JOB_DESCRIPTION)
        assert "higher" in prompt.lower() or "vaguer" in prompt.lower()


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_raises_system_exit_when_config_missing(self, tmp_path, monkeypatch):
        missing = tmp_path / "nonexistent" / "config.json"
        monkeypatch.setattr(main, "CONFIG_PATH", missing)

        with pytest.raises(SystemExit) as exc_info:
            main.load_config()

        assert exc_info.value.code == 1

    def test_prints_helpful_message_when_config_missing(self, tmp_path, monkeypatch, capsys):
        missing = tmp_path / "nonexistent" / "config.json"
        monkeypatch.setattr(main, "CONFIG_PATH", missing)

        with pytest.raises(SystemExit):
            main.load_config()

        captured = capsys.readouterr()
        assert "fitcheck" in captured.out.lower() or "config" in captured.out.lower()

    def test_returns_config_dict_when_file_exists(self, tmp_path, monkeypatch, full_config):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(full_config))
        monkeypatch.setattr(main, "CONFIG_PATH", config_file)

        result = main.load_config()

        assert result == full_config

    def test_returns_all_keys(self, tmp_path, monkeypatch, full_config):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(full_config))
        monkeypatch.setattr(main, "CONFIG_PATH", config_file)

        result = main.load_config()

        for key in full_config:
            assert key in result


# ---------------------------------------------------------------------------
# collect_risk_inputs
# ---------------------------------------------------------------------------

class TestCollectRiskInputs:
    def _run_with_inputs(self, inputs, post_interview=False):
        with patch("builtins.input", side_effect=inputs):
            return main.collect_risk_inputs(post_interview=post_interview)

    def test_returns_correct_days_posted(self):
        result = self._run_with_inputs(["30", "no", "y"])
        assert result["days_posted"] == 30

    def test_invalid_days_defaults_to_zero(self):
        result = self._run_with_inputs(["not-a-number", "no", "y"])
        assert result["days_posted"] == 0

    def test_repost_no(self):
        result = self._run_with_inputs(["7", "no", "y"])
        assert result["repost"] == "no"

    def test_repost_similar(self):
        result = self._run_with_inputs(["7", "similar", "y"])
        assert result["repost"] == "similar"

    def test_repost_exact(self):
        result = self._run_with_inputs(["7", "exact", "y"])
        assert result["repost"] == "exact"

    def test_unknown_repost_value_defaults_to_no(self):
        result = self._run_with_inputs(["7", "maybe", "y"])
        assert result["repost"] == "no"

    def test_has_timeline_yes(self):
        result = self._run_with_inputs(["7", "no", "y"])
        assert result["has_timeline"] is True

    def test_has_timeline_no(self):
        result = self._run_with_inputs(["7", "no", "n"])
        assert result["has_timeline"] is False

    def test_no_post_interview_flags_when_flag_not_set(self):
        result = self._run_with_inputs(["7", "no", "y"])
        assert result["market_research"] is False
        assert result["role_disappeared"] is False

    def test_post_interview_flags_collected_when_flag_set(self):
        result = self._run_with_inputs(["7", "no", "y", "y", "n"], post_interview=True)
        assert result["market_research"] is True
        assert result["role_disappeared"] is False

    def test_post_interview_both_flags_true(self):
        result = self._run_with_inputs(["7", "no", "y", "y", "y"], post_interview=True)
        assert result["market_research"] is True
        assert result["role_disappeared"] is True


# ---------------------------------------------------------------------------
# calculate_risk_score
# ---------------------------------------------------------------------------

class TestCalculateRiskScore:
    def _score(self, days=7, repost="no", has_timeline=True,
               market_research=False, role_disappeared=False,
               ps=3, tc=2, us=1):
        risk_inputs = {
            "days_posted": days,
            "repost": repost,
            "has_timeline": has_timeline,
            "market_research": market_research,
            "role_disappeared": role_disappeared,
        }
        jd_quality = {
            "problem_specificity": ps,
            "team_context": tc,
            "urgency_signal": us,
            "reasoning": "test",
        }
        return main.calculate_risk_score(risk_inputs, jd_quality)

    # Posting age
    def test_age_0_to_14_days_scores_0(self):
        assert self._score(days=14)["posting_age"] == 0

    def test_age_15_to_42_days_scores_10(self):
        assert self._score(days=15)["posting_age"] == 10
        assert self._score(days=42)["posting_age"] == 10

    def test_age_43_to_84_days_scores_20(self):
        assert self._score(days=43)["posting_age"] == 20
        assert self._score(days=84)["posting_age"] == 20

    def test_age_85_plus_days_scores_25(self):
        assert self._score(days=85)["posting_age"] == 25
        assert self._score(days=200)["posting_age"] == 25

    # JD quality
    def test_jd_quality_sums_sub_scores(self):
        result = self._score(ps=4, tc=3, us=2)
        assert result["jd_quality"] == 9

    def test_jd_quality_capped_at_25(self):
        result = self._score(ps=10, tc=8, us=7)
        assert result["jd_quality"] == 25

    # Repost signal
    def test_repost_no_scores_0(self):
        assert self._score(repost="no")["repost_signal"] == 0

    def test_repost_similar_scores_15(self):
        assert self._score(repost="similar")["repost_signal"] == 15

    def test_repost_exact_scores_25(self):
        assert self._score(repost="exact")["repost_signal"] == 25

    # Process signals
    def test_no_timeline_adds_8(self):
        with_timeline = self._score(has_timeline=True)["process_signals"]
        without_timeline = self._score(has_timeline=False)["process_signals"]
        assert without_timeline - with_timeline == 8

    def test_market_research_adds_10(self):
        without = self._score(market_research=False)["process_signals"]
        with_ = self._score(market_research=True)["process_signals"]
        assert with_ - without == 10

    def test_role_disappeared_adds_7(self):
        without = self._score(role_disappeared=False)["process_signals"]
        with_ = self._score(role_disappeared=True)["process_signals"]
        assert with_ - without == 7

    def test_all_process_signals_sum_to_25(self):
        result = self._score(has_timeline=False, market_research=True, role_disappeared=True)
        assert result["process_signals"] == 25

    # Total
    def test_total_is_sum_of_categories(self):
        result = self._score(days=7, repost="no", has_timeline=True, ps=3, tc=2, us=1)
        assert result["total"] == result["posting_age"] + result["jd_quality"] + result["repost_signal"] + result["process_signals"]

    def test_minimum_score_is_zero(self):
        result = self._score(days=0, repost="no", has_timeline=True, ps=0, tc=0, us=0)
        assert result["total"] == 0


# ---------------------------------------------------------------------------
# risk_label
# ---------------------------------------------------------------------------

class TestRiskLabel:
    def test_0_to_25_is_low_risk(self):
        assert "low risk" in main.risk_label(0).lower()
        assert "low risk" in main.risk_label(25).lower()

    def test_26_to_50_is_moderate_risk(self):
        assert "moderate risk" in main.risk_label(26).lower()
        assert "moderate risk" in main.risk_label(50).lower()

    def test_51_to_75_is_high_risk(self):
        assert "high risk" in main.risk_label(51).lower()
        assert "high risk" in main.risk_label(75).lower()

    def test_76_to_100_is_ghost_job(self):
        assert "ghost job" in main.risk_label(76).lower()
        assert "ghost job" in main.risk_label(100).lower()


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

class TestCheck:
    def _patch_config(self, monkeypatch, tmp_path, config):
        """Write config to a temp file and patch CONFIG_PATH."""
        config_file = tmp_path / "config.json"
        config = {**config, "jobs_dir": str(tmp_path / "jobs")}
        config_file.write_text(json.dumps(config))
        monkeypatch.setattr(main, "CONFIG_PATH", config_file)
        return config

    def test_empty_clipboard_exits_early(self, monkeypatch, tmp_path, full_config):
        self._patch_config(monkeypatch, tmp_path, full_config)

        with patch("main.pyperclip.paste", return_value=""):
            with patch("main.ollama.chat") as mock_chat:
                main.check()
                mock_chat.assert_not_called()

    def test_empty_clipboard_prints_message(self, monkeypatch, tmp_path, full_config, capsys):
        self._patch_config(monkeypatch, tmp_path, full_config)

        with patch("main.pyperclip.paste", return_value="  "):
            main.check()

        captured = capsys.readouterr()
        assert "clipboard" in captured.out.lower() or "empty" in captured.out.lower()

    def test_happy_path_writes_file_with_fit_and_risk(
        self, monkeypatch, tmp_path, full_config
    ):
        config = self._patch_config(monkeypatch, tmp_path, full_config)
        jobs_dir = Path(config["jobs_dir"])

        job_desc = "Senior Engineer role at Acme Corp."
        assessment_text = "Great fit overall."
        fit_score = 8
        filename = "acme_corp_senior_engineer.txt"

        jd_resp = make_jd_quality_response()
        fit_resp = make_ollama_response(filename, fit_score, assessment_text)

        with patch("main.pyperclip.paste", return_value=job_desc):
            with patch("main.ollama.chat", side_effect=[jd_resp, fit_resp]):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    main.check()

        expected_file = jobs_dir / filename
        assert expected_file.exists()

        content = expected_file.read_text()
        assert f"Fit: {fit_score}/10" in content
        assert "Risk:" in content
        assert "Risk Breakdown:" in content
        assert assessment_text in content
        assert job_desc in content

    def test_happy_path_prints_fit_and_risk_score(
        self, monkeypatch, tmp_path, full_config, capsys
    ):
        config = self._patch_config(monkeypatch, tmp_path, full_config)

        job_desc = "Engineer at BetaCo."
        assessment_text = "Solid candidate with room to grow."
        fit_score = 7
        filename = "betaco_engineer.txt"

        jd_resp = make_jd_quality_response()
        fit_resp = make_ollama_response(filename, fit_score, assessment_text)

        with patch("main.pyperclip.paste", return_value=job_desc):
            with patch("main.ollama.chat", side_effect=[jd_resp, fit_resp]):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    main.check()

        captured = capsys.readouterr()
        assert "7/10" in captured.out
        assert "Risk:" in captured.out
        assert assessment_text in captured.out

    def test_happy_path_prints_risk_breakdown(
        self, monkeypatch, tmp_path, full_config, capsys
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        jd_resp = make_jd_quality_response()
        fit_resp = make_ollama_response("co_role.txt", 8, "Great fit.")

        with patch("main.pyperclip.paste", return_value="Some job"):
            with patch("main.ollama.chat", side_effect=[jd_resp, fit_resp]):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    main.check()

        captured = capsys.readouterr()
        assert "Risk Breakdown:" in captured.out
        assert "/25" in captured.out

    def test_happy_path_creates_jobs_dir_if_missing(
        self, monkeypatch, tmp_path, full_config
    ):
        config = self._patch_config(monkeypatch, tmp_path, full_config)
        jobs_dir = Path(config["jobs_dir"])
        assert not jobs_dir.exists()

        jd_resp = make_jd_quality_response()
        fit_resp = make_ollama_response("co_role.txt", 9, "Excellent.")

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", side_effect=[jd_resp, fit_resp]):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    main.check()

        assert jobs_dir.exists()

    def test_jd_quality_ollama_response_error_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", side_effect=main.ollama.ResponseError("model not found")):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    with pytest.raises(SystemExit) as exc_info:
                        main.check()

        assert exc_info.value.code == 1

    def test_fit_ollama_response_error_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        jd_resp = make_jd_quality_response()

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", side_effect=[jd_resp, main.ollama.ResponseError("model not found")]):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    with pytest.raises(SystemExit) as exc_info:
                        main.check()

        assert exc_info.value.code == 1

    def test_ollama_response_error_prints_message(
        self, monkeypatch, tmp_path, full_config, capsys
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", side_effect=main.ollama.ResponseError("model not found")):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    with pytest.raises(SystemExit):
                        main.check()

        captured = capsys.readouterr()
        assert "ollama" in captured.out.lower() or "error" in captured.out.lower()

    def test_connection_error_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", side_effect=ConnectionRefusedError("connection refused")):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    with pytest.raises(SystemExit) as exc_info:
                        main.check()

        assert exc_info.value.code == 1

    def test_bad_jd_quality_json_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        bad_response = MagicMock()
        bad_response.message.content = "this is not valid json {"

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", return_value=bad_response):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    with pytest.raises(SystemExit) as exc_info:
                        main.check()

        assert exc_info.value.code == 1

    def test_missing_key_in_jd_quality_response_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        incomplete_jd = MagicMock()
        incomplete_jd.message.content = json.dumps({"problem_specificity": 5})

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", return_value=incomplete_jd):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    with pytest.raises(SystemExit) as exc_info:
                        main.check()

        assert exc_info.value.code == 1

    def test_bad_fit_json_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        jd_resp = make_jd_quality_response()
        bad_fit = MagicMock()
        bad_fit.message.content = "not valid json {"

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", side_effect=[jd_resp, bad_fit]):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    with pytest.raises(SystemExit) as exc_info:
                        main.check()

        assert exc_info.value.code == 1

    def test_missing_key_in_fit_response_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        jd_resp = make_jd_quality_response()
        incomplete_fit = MagicMock()
        incomplete_fit.message.content = json.dumps({"fit_score": 5})

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", side_effect=[jd_resp, incomplete_fit]):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    with pytest.raises(SystemExit) as exc_info:
                        main.check()

        assert exc_info.value.code == 1

    def test_uses_default_model_when_not_in_config(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)
        assert "model" not in json.loads(
            (tmp_path / "config.json").read_text()
        )

        jd_resp = make_jd_quality_response()
        fit_resp = make_ollama_response("co_role.txt", 6, "Decent fit.")

        with patch("main.pyperclip.paste", return_value="Job description text"):
            with patch("main.ollama.chat", side_effect=[jd_resp, fit_resp]) as mock_chat:
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    main.check()

        first_call_model = mock_chat.call_args_list[0].kwargs["model"]
        assert first_call_model == main.DEFAULT_MODEL

    def test_post_interview_flag_passed_to_collect_risk_inputs(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        jd_resp = make_jd_quality_response()
        fit_resp = make_ollama_response("co_role.txt", 8, "Good fit.")

        with patch("main.pyperclip.paste", return_value="Job description"):
            with patch("main.ollama.chat", side_effect=[jd_resp, fit_resp]):
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS) as mock_collect:
                    main.check(post_interview=True)

        mock_collect.assert_called_once_with(True)

    def test_jd_quality_call_uses_low_temperature(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        jd_resp = make_jd_quality_response()
        fit_resp = make_ollama_response("co_role.txt", 8, "Good fit.")

        with patch("main.pyperclip.paste", return_value="Job description"):
            with patch("main.ollama.chat", side_effect=[jd_resp, fit_resp]) as mock_chat:
                with patch("main.collect_risk_inputs", return_value=DEFAULT_RISK_INPUTS):
                    main.check()

        jd_call_kwargs = mock_chat.call_args_list[0].kwargs
        assert "options" in jd_call_kwargs
        assert jd_call_kwargs["options"].get("temperature", 1.0) < 0.5
