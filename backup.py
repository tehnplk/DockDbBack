import subprocess
import os

# Config ต้นทาง
SOURCE_CONTAINER = "postgres"  # ชื่อ container ต้นทาง
DB_NAME = "erp2"
DB_USER = "admin"
DB_PASSWORD = "112233"

# ตำแหน่งไฟล์ backup บน Windows host
HOST_BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd: list[str]) -> None:
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, shell=False)
    if result.returncode != 0:
        raise SystemExit(f"Command failed with code {result.returncode}")


def main() -> None:
    # สร้างโฟลเดอร์ /backup ใน container (ถ้ายังไม่มี)
    run(["docker", "exec", "-it", SOURCE_CONTAINER, "mkdir", "-p", "/backup"])

    # ใช้ชื่อไฟล์ dump คงที่
    container_dump_path = "/backup/erp_back.dump"

    # pg_dump ใน container
    run([
        "docker", "exec", "-e", f"PGPASSWORD={DB_PASSWORD}", "-it", SOURCE_CONTAINER,
        "pg_dump", "-U", DB_USER, "-d", DB_NAME, "-Fc", "-C", "-f", container_dump_path,
    ])

    # ดึงไฟล์ออกมาที่ Windows host (โฟลเดอร์เดียวกับสคริปต์)
    host_dump_path = os.path.join(HOST_BACKUP_DIR, "erp_back.dump")
    run(["docker", "cp", f"{SOURCE_CONTAINER}:{container_dump_path}", host_dump_path])

    print("\nBackup completed:")
    print("  Host file:", host_dump_path)


if __name__ == "__main__":
    main()
