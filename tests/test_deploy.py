"""Mechanical checks for the Docker/Compose artifacts (no daemon needed)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from healthcheck import health_url

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "deploy" / "compose.yml"


def test_health_url_uses_preset_port():
    assert health_url({"PRESET": "example"}) == "http://127.0.0.1:2443/healthz"
    assert health_url({"PRESET": "x"}) == "http://127.0.0.1:2444/healthz"


def test_health_url_port_override_and_tls(tmp_path):
    assert health_url({"PRESET": "x", "PORT": "3999"}).endswith(":3999/healthz")
    cert, key = tmp_path / "c.crt", tmp_path / "c.key"
    cert.write_text("c")
    key.write_text("k")
    env = {"PRESET": "example", "CERT_FILE": str(cert), "KEY_FILE": str(key)}
    assert health_url(env).startswith("https://")
    assert health_url({**env, "DISABLE_TLS": "1"}).startswith("http://")


def test_health_url_matches_gateway_preset_resolution(tmp_path, monkeypatch):
    """env=None must use the ambient loader semantics, even with an ambient empty PRESETS_DIR."""
    (tmp_path / "custom.toml").write_text(
        'name = "custom"\ntitle = "C"\nshort_title = "C"\nruntime = "chromium"\n'
        'target_url = "https://example.com/"\nport = 3555\nwin_w = 720\nwin_h = 720\n'
        'layout = "direct"\nrail_w = 0\ndefault_chat_x = 0\nsend_keys = ["Return"]\n'
        'paste_keys = ["ctrl+v"]\npassthrough_keys = ["Return"]\ncookie_name = "c"\n'
    )
    monkeypatch.setenv("PRESET", "custom")
    monkeypatch.setenv("PRESETS_DIR", "")
    monkeypatch.setattr("presets.DEFAULT_EXTRA_DIR", str(tmp_path))
    assert health_url().endswith(":3555/healthz")
    # An explicit empty mapping keeps the accepted M2 meaning: no extra directories.
    with pytest.raises(ValueError):
        health_url({"PRESET": "custom", "PRESETS_DIR": ""})


def test_dockerfile_wiring():
    text = (ROOT / "Dockerfile").read_text()
    assert "healthcheck.py" in text
    assert "python3-aiohttp" in text and "python3-pil" in text


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")
def test_compose_forwards_runtime_overrides(tmp_path):
    env_file = tmp_path / "app.env"
    env_file.write_text(
        "COMPOSE_PROJECT_NAME=testapp\nPRESET=x\nPORT=3444\nPROFILE_VOLUME=testapp-profile\n"
        f"CERTS_DIR={tmp_path}\nTOKEN_FILE={tmp_path}/t.txt\nPRESETS_DIR={tmp_path}\n"
        "TARGET_URL=https://example.org/\nWIN_W=800\nWIN_H=600\nJPEG_QUALITY=55\n"
        "ICON_STYLE=badge\nUPSTREAM_HOST=h.example\n"
    )
    out = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-f",
            str(COMPOSE),
            "config",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    env = json.loads(out)["services"]["app"]["environment"]
    assert env["TARGET_URL"] == "https://example.org/"
    assert (env["WIN_W"], env["WIN_H"], env["JPEG_QUALITY"], env["ICON_STYLE"]) == (
        "800",
        "600",
        "55",
        "badge",
    )
    assert env["PRESET"] == "x" and env["PORT"] == "3444"
    assert "PRESETS_DIR" not in env  # host mount path must never reach the loader


def test_extended_dockerfiles_wiring():
    term_df = ROOT / "private" / "extended" / "term" / "Dockerfile"
    wechat_df = ROOT / "private" / "extended" / "wechat" / "Dockerfile"
    if term_df.is_file():
        text = term_df.read_text()
        assert "FROM bb10-gateway-core:latest" in text
        assert "USER 1000:1000" in text
        assert "EXPOSE 2445" in text
    if wechat_df.is_file():
        text = wechat_df.read_text()
        assert "FROM bb10-gateway-core:latest" in text
        assert "USER 1000:100" in text
        assert "EXPOSE 2446" in text


def test_extended_presets_health_urls():
    fixtures = str(ROOT / "tests" / "presets.d")
    assert (
        health_url({"PRESET": "term", "PRESETS_DIR": fixtures}) == "http://127.0.0.1:2445/healthz"
    )
    assert (
        health_url({"PRESET": "wechat", "PRESETS_DIR": fixtures}) == "http://127.0.0.1:2446/healthz"
    )


def test_check_extended_images_fails_when_docker_unavailable():
    res = subprocess.run(
        [
            "bash",
            "-c",
            "docker() { return 1; }; export -f docker; bash scripts/check_extended_images.sh",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert res.returncode != 0
    assert "ERROR: required image" in res.stderr or "Docker inspect failed" in res.stderr


def test_check_extended_images_fails_on_missing_images():
    res = subprocess.run(
        [
            "bash",
            "scripts/check_extended_images.sh",
            "nonexistent-image:test",
            "nonexistent-image:test",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert res.returncode != 0
    assert "ERROR: required image 'nonexistent-image:test' is not available" in res.stderr


def test_check_extended_images_success_when_images_available():
    if shutil.which("docker") is None:
        pytest.skip("docker CLI not available")
    has_term = (
        subprocess.run(
            ["docker", "image", "inspect", "bb10-term:latest"],
            capture_output=True,
        ).returncode
        == 0
    )
    has_wechat = (
        subprocess.run(
            ["docker", "image", "inspect", "bb10-wechat:latest"],
            capture_output=True,
        ).returncode
        == 0
    )
    if not (has_term and has_wechat):
        pytest.skip("extended images not built locally")

    res = subprocess.run(
        ["bash", "scripts/check_extended_images.sh"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=90,
    )
    assert res.returncode == 0
    assert "runtime ready" in res.stdout


def test_check_extended_images_rejects_stale_readiness_scenario_a():
    """Application ready only on poll 1, gateway ready only from poll 2 must fail."""
    script = """
REVIEW_TICK=0
sleep() { REVIEW_TICK=$((REVIEW_TICK + 1)); }
docker() {
    case "$1:$2" in
        image:inspect) return 0 ;;
        run:*)
            case "$*" in
                *PRESET=term*) echo review-term ;;
                *) echo review-wechat ;;
            esac ;;
        exec:review-term)
            case "$3" in
                id) echo 'uid=1000(appuser) gid=1000(appuser)' ;;
                python3) [ "$REVIEW_TICK" -ge 2 ] ;;
                pgrep|tmux) [ "$REVIEW_TICK" -eq 1 ] ;;
                *) return 1 ;;
            esac ;;
        exec:review-wechat)
            case "$3" in
                id) echo 'uid=1000(appuser) gid=100(users)' ;;
                env) echo '0x000001 0 review WeChat' ;;
                *) return 0 ;;
            esac ;;
        *) return 0 ;;
    esac
}
export REVIEW_TICK
export -f docker sleep
bash scripts/check_extended_images.sh
"""
    res = subprocess.run(["bash", "-c", script], capture_output=True, text=True, cwd=ROOT)
    assert res.returncode != 0
    assert (
        "FAIL: term gateway and application runtime were never ready in the same poll iteration"
        in res.stderr
    )


def test_check_extended_images_rejects_stale_readiness_scenario_b():
    """Gateway ready only on poll 1, application ready only from poll 2 must fail."""
    script = """
REVIEW_TICK=0
sleep() { REVIEW_TICK=$((REVIEW_TICK + 1)); }
docker() {
    case "$1:$2" in
        image:inspect) return 0 ;;
        run:*)
            case "$*" in
                *PRESET=term*) echo review-term ;;
                *) echo review-wechat ;;
            esac ;;
        exec:review-term)
            case "$3" in
                id) echo 'uid=1000(appuser) gid=1000(appuser)' ;;
                python3) [ "$REVIEW_TICK" -eq 1 ] ;;
                pgrep|tmux) [ "$REVIEW_TICK" -ge 2 ] ;;
                *) return 1 ;;
            esac ;;
        exec:review-wechat)
            case "$3" in
                id) echo 'uid=1000(appuser) gid=100(users)' ;;
                env) echo '0x000001 0 review WeChat' ;;
                *) return 0 ;;
            esac ;;
        *) return 0 ;;
    esac
}
export REVIEW_TICK
export -f docker sleep
bash scripts/check_extended_images.sh
"""
    res = subprocess.run(["bash", "-c", script], capture_output=True, text=True, cwd=ROOT)
    assert res.returncode != 0
    assert (
        "FAIL: term gateway and application runtime were never ready in the same poll iteration"
        in res.stderr
    )


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")
def test_compose_profile_target_path(tmp_path):
    env_file = tmp_path / "app.env"
    env_file.write_text(
        "COMPOSE_PROJECT_NAME=test-wx\nPRESET=wechat\nPORT=3446\nPROFILE_VOLUME=test-wx-profile\n"
        "PROFILE_TARGET_PATH=/config\n"
        f"CERTS_DIR={tmp_path}\nTOKEN_FILE={tmp_path}/t.txt\nPRESETS_DIR={tmp_path}\n"
    )
    out = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-f",
            str(COMPOSE),
            "config",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    vols = json.loads(out)["services"]["app"]["volumes"]
    prof_vol = next(v for v in vols if v.get("source") == "profile")
    assert prof_vol["target"] == "/config"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")
def test_compose_term_extension(tmp_path):
    env_file = tmp_path / "term.env"
    env_file.write_text(
        "COMPOSE_PROJECT_NAME=test-term\nPRESET=term\nPORT=2445\nPROFILE_VOLUME=test-term-profile\n"
        f"CERTS_DIR={tmp_path}\nTOKEN_FILE={tmp_path}/t.txt\nPRESETS_DIR={tmp_path}\n"
        f"TMUX_SOCKET_DIR={tmp_path}/tmux\nHOST_WORKSPACE={tmp_path}/workspace\n"
    )
    compose_term = ROOT / "deploy" / "compose.term.yml"
    out = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-f",
            str(COMPOSE),
            "-f",
            str(compose_term),
            "config",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    data = json.loads(out)
    vols = data["services"]["app"]["volumes"]
    tmux_vol = next(v for v in vols if v.get("target") == "/tmp/tmux-1000")
    assert tmux_vol["source"] == str(tmp_path / "tmux")
    ws_vol = next(v for v in vols if v.get("target") == str(tmp_path / "workspace"))
    assert ws_vol["source"] == str(tmp_path / "workspace")


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")
def test_compose_wechat_extension(tmp_path):
    env_file = tmp_path / "wechat.env"
    env_file.write_text(
        "COMPOSE_PROJECT_NAME=test-wechat\nPRESET=wechat\nPORT=2446\nPROFILE_VOLUME=test-wx-profile\n"
        "WECHAT_HOSTNAME=test-hostname\n"
        f"CERTS_DIR={tmp_path}\nTOKEN_FILE={tmp_path}/t.txt\nPRESETS_DIR={tmp_path}\n"
    )
    compose_wechat = ROOT / "deploy" / "compose.wechat.yml"
    # Verify that ambient HOSTNAME does not override WECHAT_HOSTNAME
    ambient_env = {**os.environ, "HOSTNAME": "ambient-host"}
    ambient_env.pop("WECHAT_HOSTNAME", None)
    out = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-f",
            str(COMPOSE),
            "-f",
            str(compose_wechat),
            "config",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=ambient_env,
    ).stdout
    data = json.loads(out)
    svc = data["services"]["app"]
    assert svc["hostname"] == "test-hostname"
    assert svc["hostname"] != "ambient-host"
    assert "seccomp:unconfined" in svc.get("security_opt", [])

    # Missing WECHAT_HOSTNAME fails clearly
    bad_env_file = tmp_path / "wechat_bad.env"
    bad_env_file.write_text(
        "COMPOSE_PROJECT_NAME=test-wechat\nPRESET=wechat\nPORT=2446\nPROFILE_VOLUME=test-wx-profile\n"
        f"CERTS_DIR={tmp_path}\nTOKEN_FILE={tmp_path}/t.txt\nPRESETS_DIR={tmp_path}\n"
    )
    res = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(bad_env_file),
            "-f",
            str(COMPOSE),
            "-f",
            str(compose_wechat),
            "config",
        ],
        capture_output=True,
        text=True,
        env=ambient_env,
    )
    assert res.returncode != 0
    assert "WECHAT_HOSTNAME" in res.stderr


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")
def test_compose_discord_extension(tmp_path):
    env_file = tmp_path / "discord.env"
    env_file.write_text(
        "COMPOSE_PROJECT_NAME=test-discord\nPRESET=discord\nPORT=2443\n"
        "PROFILE_VOLUME=test-dc-profile\n"
        f"CERTS_DIR={tmp_path}\nTOKEN_FILE={tmp_path}/t.txt\nPRESETS_DIR={tmp_path}\n"
    )
    compose_discord = ROOT / "deploy" / "compose.discord.yml"
    out = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-f",
            str(COMPOSE),
            "-f",
            str(compose_discord),
            "config",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    data = json.loads(out)
    svc = data["services"]["app"]
    assert "SYS_ADMIN" in svc.get("cap_add", [])


def test_build_and_ship_cli():
    script = ROOT / "scripts" / "build_and_ship.sh"
    # --help returns 0
    help_res = subprocess.run([str(script), "--help"], capture_output=True, text=True)
    assert help_res.returncode == 0
    assert "Usage: ./scripts/build_and_ship.sh" in help_res.stdout

    # Missing host returns 2
    no_host_res = subprocess.run(
        [str(script), "--no-env"],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert no_host_res.returncode == 2
    assert "ERROR: target host is required" in no_host_res.stderr

    # Dry-run with stage mode
    dry_res = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "target.example.org",
            "--user",
            "testuser",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--stage",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert dry_res.returncode == 0
    assert (
        "=== Shipping bb10-gateway-core:latest to testuser@target.example.org ===" in dry_res.stdout
    )
    assert (
        "[dry-run] scp -O /tmp/bb10-gateway-core_latest.tar "
        "testuser@target.example.org:/tmp/bb10-gateway-core_latest.tar" in dry_res.stdout
    )

    # Dry-run with direct mode
    direct_res = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "target.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--direct",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert direct_res.returncode == 0
    assert (
        "[dry-run] docker save bb10-gateway-core:latest | ssh target.example.org"
        in direct_res.stdout
    )


def test_build_and_ship_transfer_only_and_precedence(tmp_path):
    script = ROOT / "scripts" / "build_and_ship.sh"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "calls.log"

    docker_sh = bin_dir / "docker"
    docker_sh.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "docker: $*" >> "{log_file}"\n'
        'if [ "$1" = "save" ] && [ "$3" = "-o" ]; then\n'
        '    touch "$4"\n'
        "fi\n"
        "exit 0\n"
    )
    docker_sh.chmod(0o755)

    ssh_sh = bin_dir / "ssh"
    ssh_sh.write_text(f'#!/usr/bin/env bash\necho "ssh: $*" >> "{log_file}"\nexit 0\n')
    ssh_sh.chmod(0o755)

    scp_sh = bin_dir / "scp"
    scp_sh.write_text(f'#!/usr/bin/env bash\necho "scp: $*" >> "{log_file}"\nexit 0\n')
    scp_sh.chmod(0o755)

    mock_env = {
        "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
        "TMPDIR": str(tmp_path),
    }

    # 1. Automatic mode with --no-load stages without remote load
    log_file.write_text("")
    res_auto = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--no-load",
        ],
        capture_output=True,
        text=True,
        env=mock_env,
    )
    assert res_auto.returncode == 0
    auto_log = log_file.read_text()
    assert "scp: -O" in auto_log
    assert "docker load" not in auto_log

    # 2. Explicit direct with --no-load applies precedence (stages, never loads)
    log_file.write_text("")
    res_direct_no_load = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--direct",
            "--no-load",
        ],
        capture_output=True,
        text=True,
        env=mock_env,
    )
    assert res_direct_no_load.returncode == 0
    assert "--no-load takes precedence over --direct" in res_direct_no_load.stderr
    direct_no_load_log = log_file.read_text()
    assert "scp: -O" in direct_no_load_log
    assert "docker load" not in direct_no_load_log

    # 3. Explicit staging with --no-load stages without remote load
    log_file.write_text("")
    res_stage_no_load = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--stage",
            "--no-load",
        ],
        capture_output=True,
        text=True,
        env=mock_env,
    )
    assert res_stage_no_load.returncode == 0
    stage_no_load_log = log_file.read_text()
    assert "scp: -O" in stage_no_load_log
    assert "docker load" not in stage_no_load_log

    # 4. Ordinary direct control streams directly into remote docker load
    log_file.write_text("")
    res_direct_control = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--direct",
        ],
        capture_output=True,
        text=True,
        env=mock_env,
    )
    assert res_direct_control.returncode == 0
    direct_control_log = log_file.read_text()
    assert "ssh: mock.example.org docker load" in direct_control_log

    # 5. Dry-run distinction between suggested manual import and executed command
    dry_no_load = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--no-load",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert dry_no_load.returncode == 0
    assert "(transfer-only) Suggested manual import:" in dry_no_load.stdout
    assert (
        '[dry-run] ssh -t mock.example.org "sudo /usr/local/bin/docker load'
        not in dry_no_load.stdout
    )

    dry_direct_no_load = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--direct",
            "--no-load",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert dry_direct_no_load.returncode == 0
    assert "--no-load takes precedence over --direct" in dry_direct_no_load.stderr
    assert "(transfer-only) Suggested manual import:" in dry_direct_no_load.stdout
    assert "[dry-run] docker save bb10-gateway-core:latest | ssh" not in dry_direct_no_load.stdout


def test_build_and_ship_staging_cleanup_on_failure_and_success(tmp_path):
    script = ROOT / "scripts" / "build_and_ship.sh"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_file = tmp_path / "calls.log"

    docker_sh = bin_dir / "docker"
    ssh_sh = bin_dir / "ssh"
    scp_sh = bin_dir / "scp"

    ssh_sh.write_text("#!/usr/bin/env bash\nexit 0\n")
    ssh_sh.chmod(0o755)

    mock_env = {
        "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
        "TMPDIR": str(tmp_path),
    }

    # 1. Save failure: docker save exits 31, temp archive cleaned up, exit 31 preserved
    docker_sh.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$1" = "save" ] && [ "$3" = "-o" ]; then\n'
        '    touch "$4"\n'
        "    exit 31\n"
        "fi\n"
        "exit 0\n"
    )
    docker_sh.chmod(0o755)
    scp_sh.write_text("#!/usr/bin/env bash\nexit 0\n")
    scp_sh.chmod(0o755)

    res_save_fail = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--stage",
        ],
        capture_output=True,
        text=True,
        env=mock_env,
    )
    assert res_save_fail.returncode == 31
    assert list(tmp_path.glob("bb10-ship-*.tar")) == []

    # 2. Both copy attempts fail: scp exits 32, temp archive cleaned up, exit 32 preserved
    docker_sh.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$1" = "save" ] && [ "$3" = "-o" ]; then\n'
        '    touch "$4"\n'
        "fi\n"
        "exit 0\n"
    )
    docker_sh.chmod(0o755)
    log_file.write_text("")
    scp_sh.write_text(f'#!/usr/bin/env bash\necho "scp: $*" >> "{log_file}"\nexit 32\n')
    scp_sh.chmod(0o755)

    res_copy_fail = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--stage",
        ],
        capture_output=True,
        text=True,
        env=mock_env,
    )
    assert res_copy_fail.returncode == 32
    copy_log = log_file.read_text().splitlines()
    assert len(copy_log) == 2  # both legacy scp -O and fallback scp attempted
    assert "-O" in copy_log[0].split()
    assert "-O" not in copy_log[1].split()
    assert list(tmp_path.glob("bb10-ship-*.tar")) == []

    # 3. Legacy SCP fails, fallback SCP succeeds: temp archive cleaned up, exit 0
    log_file.write_text("")
    scp_sh.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "scp: $*" >> "{log_file}"\n'
        'if [ "$1" = "-O" ]; then\n'
        "    exit 1\n"
        "fi\n"
        "exit 0\n"
    )
    scp_sh.chmod(0o755)

    res_fb_success = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--stage",
            "--no-load",
        ],
        capture_output=True,
        text=True,
        env=mock_env,
    )
    assert res_fb_success.returncode == 0
    fb_log = log_file.read_text().splitlines()
    assert len(fb_log) == 2
    assert "-O" in fb_log[0].split()
    assert "-O" not in fb_log[1].split()
    assert list(tmp_path.glob("bb10-ship-*.tar")) == []

    # 4. Successful transfer cleans up temporary archive
    log_file.write_text("")
    scp_sh.write_text(f'#!/usr/bin/env bash\necho "scp: $*" >> "{log_file}"\nexit 0\n')
    scp_sh.chmod(0o755)

    res_success = subprocess.run(
        [
            str(script),
            "--no-env",
            "--host",
            "mock.example.org",
            "--image",
            "bb10-gateway-core:latest",
            "--skip-build",
            "--stage",
            "--no-load",
        ],
        capture_output=True,
        text=True,
        env=mock_env,
    )
    assert res_success.returncode == 0
    assert list(tmp_path.glob("bb10-ship-*.tar")) == []

    # 5. Signal cancellation (SIGINT / SIGTERM): stops shipment, preserves exit code,
    # and cleans up temporary archive
    for sig, expected_rc in [("INT", 130), ("TERM", 143)]:
        docker_sh.write_text(
            "#!/usr/bin/env bash\n"
            'if [ "$1" = "save" ] && [ "$3" = "-o" ]; then\n'
            '    touch "$4"\n'
            f"    kill -s {sig} $PPID\n"
            f"    exit {expected_rc}\n"
            "fi\n"
            "exit 0\n"
        )
        docker_sh.chmod(0o755)
        scp_sh.write_text('echo "UNEXPECTED_COPY"; exit 99\n')
        scp_sh.chmod(0o755)

        res_sig = subprocess.run(
            [
                str(script),
                "--no-env",
                "--host",
                "mock.example.org",
                "--image",
                "bb10-gateway-core:latest",
                "--skip-build",
                "--stage",
                "--no-load",
            ],
            capture_output=True,
            text=True,
            env=mock_env,
        )
        assert res_sig.returncode == expected_rc
        assert "UNEXPECTED_COPY" not in res_sig.stdout
        assert list(tmp_path.glob("bb10-ship-*.tar")) == []


def test_prepare_release_rejects_dirty_worktree(tmp_path):
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Tester"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    rel_script = scripts_dir / "prepare_release.sh"
    orig_script = ROOT / "scripts" / "prepare_release.sh"
    rel_script.write_text(orig_script.read_text())
    rel_script.chmod(0o755)

    (repo / "f.txt").write_text("initial")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True)

    # Make working tree dirty
    (repo / "f.txt").write_text("dirty")
    res = subprocess.run([str(rel_script)], cwd=str(repo), capture_output=True, text=True)
    assert res.returncode == 1
    assert "working tree must be clean" in res.stderr
