"""
اسکریپت پاکسازی داده‌های اضافی از فایل‌های JSON
این اسکریپت فقط یک بار اجرا می‌شود تا مسابقاتی که در whitelist نیستند را حذف کند
"""
import json
import os

# کپی از WHITELIST از main.py
WHITELIST = {
    "انگلیس": ["لیگ برتر انگلیس", "جام حذفی انگلیس", "چمپیونشیپ انگلیس", "جام اتحادیه انگلیس", "سوپرجام انگلیس (جام خیریه)"],
    "اروپا": ["لیگ قهرمانان اروپا", "لیگ اروپا", "لیگ کنفرانس اروپا", "سوپر جام اروپا"],
    "آسیا": ["لیگ نخبگان آسیا", "لیگ قهرمانان آسیا ۲"],
    "ایتالیا": ["سری آ ایتالیا", "جام حذفی ایتالیا", "سوپر جام ایتالیا"],
    "اسپانیا": ["لالیگا اسپانیا", "کوپا دل ری اسپانیا"],
    "آلمان": ["بوندس‌لیگا آلمان", "جام حذفی آلمان"],
    "فرانسه": ["لیگ ۱ فرانسه", "جام حذفی فرانسه"],
    "برزیل": ["سری آ برزیل"],
    "عربستان سعودی": ["لیگ حرفه‌ای عربستان سعودی"],
    "ترکیه": ["سوپر لیگ ترکیه"],
    "هلند": ["لیگ برتر هلند", "جام حذفی هلند"],
    "پرتغال": ["لیگ برتر پرتغال", "جام حذفی پرتغال"],
    "اندونزی": ["سوپر لیگ اندونزی"],
}

# نرمال سازی WHITELIST
WHITELIST = {k.strip(): [l.strip() for l in v] for k, v in WHITELIST.items()}

def normalize(s):
    """حذف فاصله‌های اضافی"""
    return " ".join(s.split()).strip() if s else ""

def is_whitelisted(country, league):
    """بررسی اینکه مسابقه در لیست سفید است یا خیر"""
    country_norm = normalize(country)
    league_norm = normalize(league)
    return country_norm in WHITELIST and league_norm in WHITELIST.get(country_norm, [])

def cleanup_odds_file(filename="betforward_odds.json"):
    """پاکسازی فایل ضرایب"""
    if not os.path.exists(filename):
        print(f"❌ فایل {filename} وجود ندارد")
        return
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        original_count = len(data)
        
        # فیلتر کردن فقط مسابقات whitelist
        filtered_data = []
        for match in data:
            country = match.get("country", "Unknown")
            league = match.get("league", "Unknown")
            
            if is_whitelisted(country, league):
                filtered_data.append(match)
            else:
                print(f"  🗑️  حذف: {country} - {league} | {match.get('home_team')} vs {match.get('away_team')}")
        
        # ذخیره فایل پاکسازی شده
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=4)
        
        removed_count = original_count - len(filtered_data)
        print(f"\n✅ فایل {filename}:")
        print(f"   📊 تعداد قبل: {original_count}")
        print(f"   📊 تعداد بعد: {len(filtered_data)}")
        print(f"   🗑️  حذف شده: {removed_count}")
        
    except Exception as e:
        print(f"❌ خطا در پردازش {filename}: {e}")

def cleanup_results_file(filename="betforward_results.json"):
    """پاکسازی فایل نتایج"""
    if not os.path.exists(filename):
        print(f"❌ فایل {filename} وجود ندارد")
        return
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        original_count = len(data)
        
        # فیلتر کردن فقط مسابقات whitelist
        filtered_data = []
        for match in data:
            country = match.get("country", "Unknown")
            league = match.get("league", "Unknown")
            
            if is_whitelisted(country, league):
                filtered_data.append(match)
            else:
                print(f"  🗑️  حذف: {country} - {league} | {match.get('team1')} vs {match.get('team2')}")
        
        # ذخیره فایل پاکسازی شده
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=4)
        
        removed_count = original_count - len(filtered_data)
        print(f"\n✅ فایل {filename}:")
        print(f"   📊 تعداد قبل: {original_count}")
        print(f"   📊 تعداد بعد: {len(filtered_data)}")
        print(f"   🗑️  حذف شده: {removed_count}")
        
    except Exception as e:
        print(f"❌ خطا در پردازش {filename}: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧹 شروع پاکسازی داده‌های اضافی")
    print("="*60 + "\n")
    
    print("📁 پاکسازی فایل ضرایب...")
    print("-"*60)
    cleanup_odds_file()
    
    print("\n📁 پاکسازی فایل نتایج...")
    print("-"*60)
    cleanup_results_file()
    
    print("\n" + "="*60)
    print("✅ پاکسازی کامل شد!")
    print("="*60)
    print("\n💡 نکته: این اسکریپت را فقط یک بار اجرا کنید.")
    print("   از این به بعد، فقط مسابقات whitelist ذخیره می‌شوند.\n")
