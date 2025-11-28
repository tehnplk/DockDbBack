import subprocess
import os

# Config ปลายทาง
TARGET_CONTAINER = "erp_postgres"  # ชื่อ container ปลายทาง
TARGET_DB_NAME = "erp"            # ชื่อฐานที่ต้องการ restore ทับ
TARGET_DB_USER = "root"
TARGET_DB_PASSWORD = "112233"

# โฟลเดอร์ที่มีไฟล์ .dump บน Windows host
HOST_BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))
DUMP_FILENAME = "erp_back.dump"


def run(cmd: list[str]) -> None:
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, shell=False)
    if result.returncode != 0:
        raise SystemExit(f"Command failed with code {result.returncode}")


def main() -> None:
    dump_path = os.path.join(HOST_BACKUP_DIR, DUMP_FILENAME)
    if not os.path.exists(dump_path):
        raise SystemExit(f"Dump file not found: {dump_path}")

    file_name = os.path.basename(dump_path)
    container_dump_path = f"/backup/{file_name}"

    # สร้างโฟลเดอร์ /backup ใน container ปลายทาง (ถ้ายังไม่มี)
    run(["docker", "exec", "-it", TARGET_CONTAINER, "mkdir", "-p", "/backup"])

    # copy ไฟล์จาก Windows host เข้า container
    run(["docker", "cp", dump_path, f"{TARGET_CONTAINER}:{container_dump_path}"])

    # pg_restore ทับฐาน TARGET_DB_NAME โดยไม่ตั้ง owner จาก dump (เลี่ยง role admin)
    run([
        "docker", "exec", "-e", f"PGPASSWORD={TARGET_DB_PASSWORD}", "-it", TARGET_CONTAINER,
        "pg_restore", "-U", TARGET_DB_USER,
        "-d", TARGET_DB_NAME,
        "--clean", "--if-exists",
        "--no-owner",
        container_dump_path,
    ])

    print("\nRestore completed into DB:", TARGET_DB_NAME)


if __name__ == "__main__":
    main()
