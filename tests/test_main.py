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
# check
# ---------------------------------------------------------------------------

def make_ollama_response(filename, fit_score, assessment):
    """Build a mock ollama response object."""
    content = json.dumps({
        "filename": filename,
        "fit_score": fit_score,
        "assessment": assessment,
    })
    response = MagicMock()
    response.message.content = content
    return response


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

    def test_happy_path_writes_file_with_correct_format(
        self, monkeypatch, tmp_path, full_config
    ):
        config = self._patch_config(monkeypatch, tmp_path, full_config)
        jobs_dir = Path(config["jobs_dir"])

        job_desc = "Senior Engineer role at Acme Corp."
        assessment_text = "Great fit overall."
        fit_score = 8
        filename = "acme_corp_senior_engineer.txt"

        mock_response = make_ollama_response(filename, fit_score, assessment_text)

        with patch("main.pyperclip.paste", return_value=job_desc):
            with patch("main.ollama.chat", return_value=mock_response):
                main.check()

        expected_file = jobs_dir / filename
        assert expected_file.exists()

        content = expected_file.read_text()
        assert content == f"Fit: {fit_score}/10\n\n{assessment_text}\n\n---\n\n{job_desc}"

    def test_happy_path_prints_score_and_assessment(
        self, monkeypatch, tmp_path, full_config, capsys
    ):
        config = self._patch_config(monkeypatch, tmp_path, full_config)

        job_desc = "Engineer at BetaCo."
        assessment_text = "Solid candidate with room to grow."
        fit_score = 7
        filename = "betaco_engineer.txt"

        mock_response = make_ollama_response(filename, fit_score, assessment_text)

        with patch("main.pyperclip.paste", return_value=job_desc):
            with patch("main.ollama.chat", return_value=mock_response):
                main.check()

        captured = capsys.readouterr()
        assert "7/10" in captured.out
        assert assessment_text in captured.out

    def test_happy_path_creates_jobs_dir_if_missing(
        self, monkeypatch, tmp_path, full_config
    ):
        config = self._patch_config(monkeypatch, tmp_path, full_config)
        jobs_dir = Path(config["jobs_dir"])
        assert not jobs_dir.exists()

        mock_response = make_ollama_response("co_role.txt", 9, "Excellent.")

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", return_value=mock_response):
                main.check()

        assert jobs_dir.exists()

    def test_ollama_response_error_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch(
                "main.ollama.chat",
                side_effect=main.ollama.ResponseError("model not found"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main.check()

        assert exc_info.value.code == 1

    def test_ollama_response_error_prints_message(
        self, monkeypatch, tmp_path, full_config, capsys
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch(
                "main.ollama.chat",
                side_effect=main.ollama.ResponseError("model not found"),
            ):
                with pytest.raises(SystemExit):
                    main.check()

        captured = capsys.readouterr()
        assert "ollama" in captured.out.lower() or "error" in captured.out.lower()

    def test_connection_error_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch(
                "main.ollama.chat",
                side_effect=ConnectionRefusedError("connection refused"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main.check()

        assert exc_info.value.code == 1

    def test_bad_json_from_model_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        bad_response = MagicMock()
        bad_response.message.content = "this is not valid json {"

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", return_value=bad_response):
                with pytest.raises(SystemExit) as exc_info:
                    main.check()

        assert exc_info.value.code == 1

    def test_missing_key_in_model_response_exits_with_code_1(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)

        incomplete_response = MagicMock()
        # Valid JSON but missing required keys
        incomplete_response.message.content = json.dumps({"fit_score": 5})

        with patch("main.pyperclip.paste", return_value="Some job description"):
            with patch("main.ollama.chat", return_value=incomplete_response):
                with pytest.raises(SystemExit) as exc_info:
                    main.check()

        assert exc_info.value.code == 1

    def test_uses_default_model_when_not_in_config(
        self, monkeypatch, tmp_path, full_config
    ):
        self._patch_config(monkeypatch, tmp_path, full_config)
        # Verify the config written by _patch_config has no "model" key
        assert "model" not in json.loads(
            (tmp_path / "config.json").read_text()
        )

        mock_response = make_ollama_response("co_role.txt", 6, "Decent fit.")

        with patch("main.pyperclip.paste", return_value="Job description text"):
            with patch("main.ollama.chat", return_value=mock_response) as mock_chat:
                main.check()

        # ollama.chat is called with model= as a keyword argument
        called_model = mock_chat.call_args.kwargs["model"]
        assert called_model == main.DEFAULT_MODEL
