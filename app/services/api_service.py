import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta

class KrxApiService:
    def __init__(self):
        self.base_url = "https://data-dbg.krx.co.kr/svc/apis"
        self.api_key = "73346D637E1B47AA8B653668D4D969288CEAB195"
        self.timeout = 30.0

    async def _fetch_krx_data(self, endpoint: str, bas_dd: Optional[str] = None) -> List:
        """
        데이터를 조회한 후 OutBlock_1 내부의 리스트만 반환합니다.
        """
        url = f"{self.base_url}{endpoint}"
        if bas_dd is None:
            current_date = datetime.now()
        else:
            current_date = datetime.strptime(bas_dd, "%Y%m%d")

        max_retries = 7
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for day_offset in range(max_retries):
                target_date = current_date - timedelta(days=day_offset)
                target_date_str = target_date.strftime("%Y%m%d")
                
                params = {
                    "AUTH_KEY": self.api_key,
                    "basDd": target_date_str
                }
                
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()
                    
                    # 명세서 구조: result["OutBlock_1"]이 리스트여야 함
                    if "OutBlock_1" in result and isinstance(result["OutBlock_1"], list):
                        if len(result["OutBlock_1"]) > 0:
                            print(f"✅ KRX 데이터 추출 성공 ({target_date_str}): {len(result['OutBlock_1'])}건")
                            # 핵심: 딕셔너리 전체가 아닌 실제 데이터 리스트만 반환
                            return result["OutBlock_1"]
                    
                    print(f"⚠️ {target_date_str} 응답에 OutBlock_1 데이터가 비어있음")
                except Exception as e:
                    continue
            
            return [] # 데이터가 없으면 빈 리스트 반환

    async def fetch_kospi_index(self, bas_dd: Optional[str] = None) -> List:
        """코스피 지수 데이터 리스트 반환"""
        return await self._fetch_krx_data("/idx/krx_dd_trd", bas_dd)
    
    async def fetch_kosdaq_index(self, bas_dd: Optional[str] = None) -> List:
        """코스닥 지수 데이터 리스트 반환"""
        return await self._fetch_krx_data("/idx/krx_dd_trd", bas_dd)

krx_api_service = KrxApiService()