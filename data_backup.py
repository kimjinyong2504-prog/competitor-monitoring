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
        
        # 원격 저장소 확인 및 설정
        remote_check = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if remote_check.returncode != 0:
            # 원격 저장소가 없으면 환경 변수에서 가져오거나 기본값 사용
            github_repo = os.environ.get('GITHUB_REPO', '')
            if not github_repo:
                # 환경 변수에서 저장소 정보 추출 시도
                github_repo = os.environ.get('RENDER_GIT_REPO', '')
                if not github_repo:
                    print("[백업] 원격 저장소가 설정되지 않았습니다.")
                    print("[백업] GITHUB_REPO 환경 변수를 설정하거나 원격 저장소를 수동으로 추가하세요.")
                    return False
            
            # 원격 저장소 추가
            if not github_repo.startswith('http'):
                github_repo = f'https://github.com/{github_repo}.git'
            
            subprocess.run(['git', 'remote', 'add', 'origin', github_repo], cwd=os.getcwd(), check=False)
            print(f"[백업] 원격 저장소 설정: {github_repo}")
        
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
        
        # Git 사용자 정보 설정 (환경 변수 우선, 없으면 기본값 사용)
        user_name = os.environ.get('GIT_USER_NAME', '')
        user_email = os.environ.get('GIT_USER_EMAIL', '')
        
        # 환경 변수가 없으면 Git 설정에서 가져오기
        if not user_name:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            user_name = result.stdout.strip()
        
        if not user_email:
            result = subprocess.run(
                ['git', 'config', 'user.email'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            user_email = result.stdout.strip()
        
        # 여전히 없으면 기본값 사용
        if not user_name:
            user_name = os.environ.get('GIT_USER_NAME', 'GitHub Backup')
        if not user_email:
            user_email = os.environ.get('GIT_USER_EMAIL', 'backup@noreply.github.com')
        
        # Git 설정에 명시적으로 설정
        subprocess.run(['git', 'config', 'user.name', user_name], cwd=os.getcwd(), check=False)
        subprocess.run(['git', 'config', 'user.email', user_email], cwd=os.getcwd(), check=False)
        
        print(f"[백업] Git 사용자 정보: {user_name} <{user_email}>")
        
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
        remote_url_result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if remote_url_result.returncode != 0:
            print("[백업] 원격 저장소 URL을 가져올 수 없습니다.")
            return False
        
        remote_url = remote_url_result.stdout.strip()
        
        if github_token and remote_url.startswith('https://') and 'github.com' in remote_url:
            # HTTPS URL에 토큰 추가
            auth_url = remote_url.replace('https://', f'https://{github_token}@')
            subprocess.run(['git', 'remote', 'set-url', 'origin', auth_url], cwd=os.getcwd(), check=False)
            print("[백업] GitHub 토큰을 사용하여 인증 설정")
        
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
        # Git이 초기화되어 있는지 확인
        if not os.path.exists('.git'):
            print("[복원] Git 저장소가 초기화되지 않았습니다.")
            return False
        
        # Git 사용자 정보 설정 (복원 시에도 필요)
        user_name = os.environ.get('GIT_USER_NAME', 'GitHub Backup')
        user_email = os.environ.get('GIT_USER_EMAIL', 'backup@noreply.github.com')
        subprocess.run(['git', 'config', 'user.name', user_name], cwd=os.getcwd(), check=False)
        subprocess.run(['git', 'config', 'user.email', user_email], cwd=os.getcwd(), check=False)
        
        # 원격 저장소 확인 및 설정
        remote_check = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if remote_check.returncode != 0:
            # 원격 저장소가 없으면 환경 변수에서 가져오거나 기본값 사용
            github_repo = os.environ.get('GITHUB_REPO', '')
            if not github_repo:
                github_repo = os.environ.get('RENDER_GIT_REPO', '')
                if not github_repo:
                    print("[복원] 원격 저장소가 설정되지 않았습니다.")
                    return False
            
            if not github_repo.startswith('http'):
                github_repo = f'https://github.com/{github_repo}.git'
            
            subprocess.run(['git', 'remote', 'add', 'origin', github_repo], cwd=os.getcwd(), check=False)
            print(f"[복원] 원격 저장소 설정: {github_repo}")
        
        # GitHub 토큰이 있으면 인증 설정
        github_token = os.environ.get('GITHUB_TOKEN', '')
        remote_url_result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if remote_url_result.returncode == 0:
            remote_url = remote_url_result.stdout.strip()
            if github_token and remote_url.startswith('https://') and 'github.com' in remote_url:
                auth_url = remote_url.replace('https://', f'https://{github_token}@')
                subprocess.run(['git', 'remote', 'set-url', 'origin', auth_url], cwd=os.getcwd(), check=False)
                print("[복원] GitHub 토큰을 사용하여 인증 설정")
        
        # Git fetch 및 pull
        print("[복원] GitHub에서 최신 데이터 가져오는 중...")
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin', 'main'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        pull_result = subprocess.run(
            ['git', 'pull', 'origin', 'main', '--no-edit'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if pull_result.returncode == 0:
            print("[복원 성공] GitHub에서 최신 데이터를 가져왔습니다.")
            # 복원된 파일 확인
            data_files = [
                '251215/data.json',
                '251215/deleted_articles.json',
                '251215_yuil/data.json',
                '251215_yuil/deleted_articles.json',
                '251215_aia/data.json',
                '251215_aia/deleted_articles.json'
            ]
            restored = [f for f in data_files if os.path.exists(f)]
            if restored:
                print(f"[복원] 복원된 파일: {', '.join(restored)}")
            return True
        else:
            print(f"[복원 실패] {pull_result.stderr}")
            if pull_result.stdout:
                print(f"[복원] stdout: {pull_result.stdout}")
            return False
            
    except Exception as e:
        print(f"[복원 오류] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

