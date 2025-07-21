import json
import random
from pathlib import Path
from typing import Dict, List

def map_accounts_to_folders():
    """accounts.json의 이메일과 choom 폴더를 랜덤으로 매핑"""
    
    # accounts.json 로드
    accounts_file = Path("accounts.json")
    if not accounts_file.exists():
        print("❌ accounts.json 파일을 찾을 수 없습니다.")
        return
    
    with accounts_file.open('r', encoding='utf-8') as f:
        accounts_data = json.load(f)
    
    emails = accounts_data.get('emails', [])
    password = accounts_data.get('password', ['test1234!@#$'])[0]
    
    # choom 폴더 내 폴더명 가져오기
    choom_path = Path("/Users/minsung/Documents/choom-macro/choom")
    if not choom_path.exists():
        print("❌ choom 폴더를 찾을 수 없습니다.")
        return
    
    folders = [f.name for f in choom_path.iterdir() if f.is_dir()]
    print(f"📁 발견된 폴더: {folders}")
    
    # 기존 매핑 로드 (있다면)
    mapped_accounts = []
    existing_mappings = {}
    used_folders = set()
    
    if 'mappings' in accounts_data:
        for mapping in accounts_data['mappings']:
            email = mapping.get('email')
            folder = mapping.get('folder')
            if email and folder:
                existing_mappings[email] = folder
                used_folders.add(folder)
                mapped_accounts.append(mapping)
        print(f"📋 기존 매핑 {len(existing_mappings)}개 발견")
    
    # 사용 가능한 폴더 (이미 매핑되지 않은 폴더)
    available_folders = [f for f in folders if f not in used_folders]
    random.shuffle(available_folders)  # 랜덤 섞기
    
    print(f"🎲 매핑 가능한 폴더: {available_folders}")
    
    # 새로운 매핑 생성
    folder_index = 0
    for email in emails:
        if email in existing_mappings:
            # 이미 매핑된 계정은 건너뛰기
            print(f"✅ {email} → {existing_mappings[email]} (기존 매핑)")
            continue
        
        if folder_index >= len(available_folders):
            print(f"⚠️ {email}: 매핑할 폴더가 부족합니다.")
            mapped_accounts.append({
                "email": email,
                "password": password,
                "folder": None,
                "uploaded_count": 0
            })
            continue
        
        # 새로운 매핑 생성
        assigned_folder = available_folders[folder_index]
        folder_index += 1
        
        mapped_accounts.append({
            "email": email,
            "password": password,
            "folder": assigned_folder,
            "uploaded_count": 0
        })
        
        print(f"🆕 {email} → {assigned_folder} (새 매핑)")
    
    # 결과 저장
    result = {
        "emails": emails,
        "password": [password],
        "mappings": mapped_accounts
    }
    
    with accounts_file.open('w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 매핑 완료! {len(mapped_accounts)}개 계정 처리")
    print(f"📄 accounts.json 업데이트 완료")
    
    # 요약 출력
    print(f"\n📊 매핑 요약:")
    for mapping in mapped_accounts:
        email = mapping['email']
        folder = mapping['folder']
        if folder:
            print(f"  {email} → {folder}")
        else:
            print(f"  {email} → (폴더 없음)")

if __name__ == "__main__":
    map_accounts_to_folders()