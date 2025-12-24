"""
일정 관련 외부 API 호출을 담당하는 서비스 모듈
"""
import httpx
from typing import List, Dict
from datetime import datetime


class ScheduleApiService:
    """일정 관련 외부 API 호출 서비스"""
    
    def __init__(self):
        self.api_url = "https://api.example.com/schedules"  # 실제 API URL로 변경 필요
        self.timeout = 30.0
    
    async def fetch_schedules_from_api(self) -> List[Dict]:
        """
        외부 API에서 일정 데이터를 가져옵니다.
        
        Returns:
            List[Dict]: 일정 데이터 리스트 (id, date, title, type 포함)
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url)
                response.raise_for_status()
                data = response.json()
                
                # API 응답을 일정 형식으로 변환
                schedules = []
                for item in data:
                    schedules.append({
                        "date": item.get("date"),
                        "title": item.get("title", ""),
                        "type": "api"  # API에서 가져온 데이터임을 표시
                    })
                
                return schedules
        except httpx.HTTPError as e:
            print(f"일정 API 호출 실패: {e}")
            return []
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return []


# 싱글톤 인스턴스
schedule_api_service = ScheduleApiService()

