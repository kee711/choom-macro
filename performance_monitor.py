#!/usr/bin/env python3
"""
업로드 성능 모니터링 도구
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# src 모듈을 import하기 위해 경로 추가
sys.path.append(str(Path(__file__).parent / "src"))

def analyze_upload_performance():
    """업로드 성능 분석"""
    print("⚡ Upload Performance Monitor")
    print("=" * 50)
    
    # 로그 파일들 확인
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("❌ Logs directory not found")
        return
    
    app_log = logs_dir / "app.log"
    retry_log = logs_dir / "retry.log"
    uploaded_files = logs_dir / "uploaded_files.json"
    
    print("📊 CURRENT CONFIGURATION")
    print("-" * 30)
    
    # 현재 설정 읽기
    config_file = Path("config/config.json")
    if config_file.exists():
        try:
            with config_file.open('r') as f:
                config = json.load(f)
            
            upload_delay = config.get('general', {}).get('upload_delay_seconds', 'N/A')
            implicit_wait = config.get('web_automation', {}).get('implicit_wait', 'N/A')
            print(f"⏱️ Upload delay: {upload_delay} seconds")
            print(f"⏳ Implicit wait: {implicit_wait} seconds")
        except Exception as e:
            print(f"❌ Error reading config: {e}")
    
    # 업로드된 파일 통계
    if uploaded_files.exists():
        try:
            with uploaded_files.open('r') as f:
                data = json.load(f)
            
            print(f"\n📈 UPLOAD STATISTICS")
            print("-" * 30)
            
            total_uploads = 0
            accounts_with_uploads = 0
            uploads_by_date = defaultdict(int)
            
            for email, files in data.items():
                if files:
                    accounts_with_uploads += 1
                    total_uploads += len(files)
                    
                    # 날짜별 업로드 수 계산
                    for filename, info in files.items():
                        upload_date = info.get('upload_date', '')
                        if upload_date:
                            try:
                                date_obj = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                                date_str = date_obj.strftime('%Y-%m-%d')
                                uploads_by_date[date_str] += 1
                            except:
                                pass
            
            print(f"📱 Active accounts: {accounts_with_uploads}")
            print(f"📊 Total uploads: {total_uploads}")
            
            if uploads_by_date:
                print(f"\n📅 UPLOADS BY DATE")
                print("-" * 20)
                for date, count in sorted(uploads_by_date.items()):
                    print(f"{date}: {count} uploads")
                
                # 최근 7일 평균
                recent_dates = sorted(uploads_by_date.keys())[-7:]
                if recent_dates:
                    recent_total = sum(uploads_by_date[date] for date in recent_dates)
                    avg_per_day = recent_total / len(recent_dates)
                    print(f"\n📊 Recent 7-day average: {avg_per_day:.1f} uploads/day")
            
        except Exception as e:
            print(f"❌ Error analyzing uploaded files: {e}")
    
    # 재시작 통계
    if retry_log.exists():
        try:
            with retry_log.open('r') as f:
                retry_lines = f.readlines()
            
            restart_count = sum(1 for line in retry_lines if 'main.py failed' in line)
            success_count = sum(1 for line in retry_lines if 'completed successfully' in line)
            
            print(f"\n🔄 RESTART STATISTICS")
            print("-" * 20)
            print(f"🔄 Total restarts: {restart_count}")
            print(f"✅ Successful completions: {success_count}")
            
            if restart_count + success_count > 0:
                success_rate = (success_count / (restart_count + success_count)) * 100
                print(f"📈 Success rate: {success_rate:.1f}%")
        
        except Exception as e:
            print(f"❌ Error analyzing retry log: {e}")
    
    print(f"\n⚡ SPEED OPTIMIZATION RECOMMENDATIONS")
    print("-" * 40)
    print("✅ Current optimizations applied:")
    print("   • Reduced upload delay to 2 seconds")
    print("   • Optimized browser options")
    print("   • Disabled image loading")
    print("   • Reduced implicit wait to 8 seconds")
    print("   • Faster restart delay (5 seconds)")
    print("   • High confidence filtering")
    print("   • 50 uploads per account limit")
    
    print(f"\n🎯 FURTHER OPTIMIZATION IDEAS")
    print("-" * 30)
    print("1. 🏃‍♂️ Reduce upload_delay_seconds to 1 second")
    print("2. 🚀 Enable headless mode for faster browsing")
    print("3. 🔄 Reduce restart delay to 3 seconds")
    print("4. 🎯 Pre-filter files before processing")
    print("5. 📱 Optimize mobile emulation settings")
    
    print(f"\n⚠️ STABILITY NOTES")
    print("-" * 20)
    print("• Monitor restart frequency")
    print("• Keep success rate above 80%")
    print("• Watch for timeout errors")
    print("• Ensure upload completion")

def recommend_optimal_settings():
    """최적 설정 추천"""
    print(f"\n🎛️ RECOMMENDED SETTINGS")
    print("=" * 30)
    print("For MAXIMUM SPEED (less stable):")
    print("  upload_delay_seconds: 1")
    print("  implicit_wait: 6")
    print("  retry_delay: 3")
    print("  headless: true")
    print()
    print("For BALANCED (current):")
    print("  upload_delay_seconds: 2")
    print("  implicit_wait: 8") 
    print("  retry_delay: 5")
    print("  headless: false")
    print()
    print("For MAXIMUM STABILITY:")
    print("  upload_delay_seconds: 3")
    print("  implicit_wait: 10")
    print("  retry_delay: 10")
    print("  headless: false")

if __name__ == '__main__':
    analyze_upload_performance()
    recommend_optimal_settings()