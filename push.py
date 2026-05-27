import os
from datetime import datetime

def run(cmd):
    print(f"→ {cmd}")
    result = os.system(cmd)
    return result == 0

def main():
    print("="*70)
    print("🚀 AI Study 2026 - Auto Push Tool (Phiên bản ổn định)")
    print("="*70)
    
    message = input("\nNhập commit message (Enter = dùng mặc định): ").strip()
    if not message:
        message = f"Update at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    print(f"\n📤 Commit: {message}\n")
    
    # Thứ tự an toàn hơn
    commands = [
        ("git add .", "Thêm file thay đổi"),
        (f'git commit -m "{message}"', "Commit thay đổi"),
        ("git pull origin main --rebase", "Kéo code mới từ GitHub"),
        ("git push", "Đẩy lên GitHub")
    ]
    
    for cmd, desc in commands:
        print(f"🔄 {desc}...")
        if not run(cmd):
            print(f"❌ Lỗi ở bước: {desc}")
            
            if "pull" in cmd or "rebase" in cmd:
                print("\n⚠️  Có conflict. Đang thử cách khác...")
                os.system("git rebase --abort")
                os.system("git pull origin main")
                if run("git push"):
                    print("✅ Push thành công sau khi pull!")
                else:
                    print("❌ Vẫn lỗi. Bạn cần xử lý conflict thủ công.")
            break
    else:
        print("\n✅ HOÀN TẤT! Code đã được đẩy lên GitHub.")
        print("App Streamlit sẽ tự rebuild trong 30-60 giây.")

if __name__ == "__main__":
    main()
    input("\nNhấn Enter để đóng...")