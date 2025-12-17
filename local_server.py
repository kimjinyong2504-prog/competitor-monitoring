#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로컬 웹 서버 - HTML 보고서 자동 업데이트용
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os
import json
import subprocess
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)  # CORS 허용

DATA_FILE = "hwasung_rna_data.json"
REPORT_FILE = "hwasung_rna_report.html"

@app.route('/')
def index():
    """HTML 보고서 반환"""
    if os.path.exists(REPORT_FILE):
        return send_file(REPORT_FILE)
    return "보고서 파일을 찾을 수 없습니다.", 404

@app.route('/api/status')
def get_status():
    """데이터 상태 확인"""
    status = {
        "data_exists": os.path.exists(DATA_FILE),
        "report_exists": os.path.exists(REPORT_FILE),
        "last_updated": None,
        "data_size": 0,
        "report_size": 0
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                status["last_updated"] = data.get("last_updated")
                status["data_size"] = os.path.getsize(DATA_FILE)
        except:
            pass
    
    if os.path.exists(REPORT_FILE):
        status["report_size"] = os.path.getsize(REPORT_FILE)
        # 파일 수정 시간
        status["report_modified"] = datetime.fromtimestamp(
            os.path.getmtime(REPORT_FILE)
        ).strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify(status)

@app.route('/api/update', methods=['POST'])
def update_report():
    """보고서 업데이트 요청"""
    try:
        # main.py 실행
        result = subprocess.run(
            ["python", "main.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        return jsonify({
            "success": result.returncode == 0,
            "message": "업데이트 완료" if result.returncode == 0 else "업데이트 실패",
            "output": result.stdout,
            "error": result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "message": "업데이트 시간 초과"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류: {str(e)}"
        }), 500

@app.route('/api/data')
def get_data():
    """JSON 데이터 반환"""
    if os.path.exists(DATA_FILE):
        return send_file(DATA_FILE, mimetype='application/json')
    return jsonify({"error": "데이터 파일을 찾을 수 없습니다."}), 404

def auto_update_worker():
    """백그라운드 자동 업데이트"""
    while True:
        try:
            time.sleep(3600)  # 1시간마다
            print(f"[{datetime.now()}] 자동 업데이트 실행...")
            subprocess.run(["python", "main.py"], timeout=300)
        except Exception as e:
            print(f"자동 업데이트 오류: {e}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="화승알앤에이 보고서 로컬 서버")
    parser.add_argument("--port", "-p", type=int, default=5000, help="포트 번호 (기본: 5000)")
    parser.add_argument("--host", default="127.0.0.1", help="호스트 (기본: 127.0.0.1)")
    parser.add_argument("--auto-update", action="store_true", help="백그라운드 자동 업데이트 활성화")
    args = parser.parse_args()
    
    if args.auto_update:
        # 백그라운드 자동 업데이트 스레드 시작
        update_thread = threading.Thread(target=auto_update_worker, daemon=True)
        update_thread.start()
        print("백그라운드 자동 업데이트가 활성화되었습니다.")
    
    print(f"서버 시작: http://{args.host}:{args.port}")
    print(f"보고서 보기: http://{args.host}:{args.port}/")
    print("종료하려면 Ctrl+C를 누르세요.")
    
    app.run(host=args.host, port=args.port, debug=False)

