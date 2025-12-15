#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 백업 유틸리티 - GitHub에 자동 커밋/푸시
"""

import os
import subprocess
import json
from pathlib import Path

def backup_to_github():
    """데이터 파일을 GitHub에 백업"""
    try:
        # Git이 초기화되어 있는지 확인
        if not os.path.exists('.git'):
            print("[백업] Git 저장소가 초기화되지 않았습니다.")
            return False
        
        # 변경된 데이터 파일 확인
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        # 데이터 파일만 필터링
        data_files = []
        for line in result.stdout.strip().split('\n'):
            if line and any(x in line for x in ['data.json', 'deleted_articles.json']):
                data_files.append(line.split()[-1])
        
        if not data_files:
            print("[백업] 백업할 데이터 파일이 없습니다.")
            return True
        
        # Git 사용자 정보 확인
        user_name = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        ).stdout.strip()
        
        user_email = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        ).stdout.strip()
        
        if not user_name or not user_email:
            print("[백업] Git 사용자 정보가 설정되지 않았습니다.")
            return False
        
        # 파일 추가
        for file in data_files:
            subprocess.run(['git', 'add', file], cwd=os.getcwd(), check=False)
        
        # 커밋
        commit_message = f"Auto backup: Update data files"
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=os.getcwd(),
            check=False
        )
        
        # 푸시 (GitHub Personal Access Token 사용 가능)
        # 환경 변수에서 GitHub 토큰 확인
        github_token = os.environ.get('GITHUB_TOKEN', '')
        if github_token:
            # 토큰을 사용한 푸시
            remote_url = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            ).stdout.strip()
            
            if remote_url.startswith('https://'):
                # HTTPS URL에 토큰 추가
                if 'github.com' in remote_url:
                    auth_url = remote_url.replace('https://', f'https://{github_token}@')
                    subprocess.run(['git', 'remote', 'set-url', 'origin', auth_url], cwd=os.getcwd(), check=False)
        
        push_result = subprocess.run(
            ['git', 'push', 'origin', 'main'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if push_result.returncode == 0:
            print(f"[백업 성공] {len(data_files)}개의 파일을 GitHub에 백업했습니다.")
            return True
        else:
            print(f"[백업 실패] {push_result.stderr}")
            return False
            
    except Exception as e:
        print(f"[백업 오류] {str(e)}")
        return False

def load_from_github():
    """GitHub에서 최신 데이터 파일 가져오기"""
    try:
        # Git pull
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print("[복원 성공] GitHub에서 최신 데이터를 가져왔습니다.")
            return True
        else:
            print(f"[복원 실패] {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[복원 오류] {str(e)}")
        return False

