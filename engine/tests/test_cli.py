from __future__ import annotations

import json
from pathlib import Path

import pytest

from seo_engine.cli import main

FIX = Path(__file__).parent / "fixtures"


def test_cli_keywords_discover(capsys):
    rc = main(["keywords", str(FIX / "competitor_a.html"), str(FIX / "competitor_b.html")])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "discover"
    assert out["keywords"]


def test_cli_keywords_gap(capsys):
    rc = main(
        [
            "keywords",
            str(FIX / "competitor_a.html"),
            str(FIX / "competitor_b.html"),
            "--own",
            str(FIX / "own_page.html"),
        ]
    )
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "gap"


def test_cli_links_dryrun_then_apply(tmp_path, capsys):
    pages = [str(FIX / "competitor_a.html"), str(FIX / "competitor_b.html")]
    # dry-run
    assert main(["links", *pages, "--min-relevance", "0.0"]) == 0
    dry = json.loads(capsys.readouterr().out)
    assert dry["mode"] == "recommend"
    assert "recommendations" in dry

    # apply writes to a NEW dir, never in place
    out_dir = tmp_path / "edited"
    assert main(["links", *pages, "--min-relevance", "0.0", "--apply",
                 "--write-dir", str(out_dir)]) == 0
    applied = json.loads(capsys.readouterr().out)
    assert applied["mode"] == "apply"
    # original fixtures untouched
    assert (FIX / "competitor_a.html").read_text()


def test_cli_alt_audit_and_apply(tmp_path, capsys):
    page = str(FIX / "page_with_images.html")
    assert main(["alt", page]) == 0
    audit = json.loads(capsys.readouterr().out)
    assert audit["mode"] == "audit"

    out_dir = tmp_path / "alt_edited"
    assert main(["alt", page, "--apply", "--write-dir", str(out_dir)]) == 0
    applied = json.loads(capsys.readouterr().out)
    assert applied["mode"] == "apply"
    # at least one edited file produced
    assert list(out_dir.glob("*.alttext.html"))


def test_cli_requires_subcommand():
    with pytest.raises(SystemExit):
        main([])
