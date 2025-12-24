"""
금융위원회 공개데이터포털 API 호출을 담당하는 서비스 모듈
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime


class FinanceApiService:
    """금융위원회 공개데이터포털 API 호출 서비스"""
    
    def __init__(self):
        self.base_url = "http://apis.data.go.kr/1160100/service"
        self.service_key = "4614abeae6a355ee62d9d9ac6ff0799dae33fca08be8939ee0199563ac8e2f61"
        self.timeout = 30.0
    
    async def fetch_disclosure_info(self, page_no: int = 1, num_of_rows: int = 10) -> Dict:
        """
        금융위원회 공시정보를 가져옵니다.
        
        Args:
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 한 페이지당 결과 수 (기본값: 10)
        
        Returns:
            Dict: 공시정보 데이터
        """
        try:
            url = f"{self.base_url}/GetDiscInfoService_V2/getDiscInfo"
            params = {
                "serviceKey": self.service_key,
                "resultType": "json",
                "pageNo": page_no,
                "numOfRows": num_of_rows
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"공시정보 API 호출 실패: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return {"error": str(e)}
    
    async def fetch_stock_issuance_info(self, page_no: int = 1, num_of_rows: int = 10) -> Dict:
        """
        금융위원회 주식발행 공시정보를 가져옵니다.
        
        Args:
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 한 페이지당 결과 수 (기본값: 10)
        
        Returns:
            Dict: 주식발행 공시정보 데이터
        """
        try:
            url = f"{self.base_url}/GetStockIssuanceInfoService/getStockIssuanceInfo"
            params = {
                "serviceKey": self.service_key,
                "resultType": "json",
                "pageNo": page_no,
                "numOfRows": num_of_rows
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"주식발행 공시정보 API 호출 실패: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return {"error": str(e)}
    
    async def fetch_stock_price_info(self, page_no: int = 1, num_of_rows: int = 10) -> Dict:
        """
        금융위원회 주식시세정보를 가져옵니다.
        
        Args:
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 한 페이지당 결과 수 (기본값: 10)
        
        Returns:
            Dict: 주식시세정보 데이터
        """
        try:
            url = f"{self.base_url}/GetStockPriceInfoService/getStockPriceInfo"
            params = {
                "serviceKey": self.service_key,
                "resultType": "json",
                "pageNo": page_no,
                "numOfRows": num_of_rows
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"주식시세정보 API 호출 실패: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return {"error": str(e)}
    
    async def fetch_all_finance_data(self, page_no: int = 1, num_of_rows: int = 10) -> Dict:
        """
        모든 금융위원회 데이터를 한번에 가져옵니다.
        
        Args:
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 한 페이지당 결과 수 (기본값: 10)
        
        Returns:
            Dict: 모든 데이터를 포함한 딕셔너리
        """
        disclosure = await self.fetch_disclosure_info(page_no, num_of_rows)
        issuance = await self.fetch_stock_issuance_info(page_no, num_of_rows)
        price = await self.fetch_stock_price_info(page_no, num_of_rows)
        
        return {
            "disclosure": disclosure,
            "issuance": issuance,
            "price": price,
            "fetched_at": datetime.now().isoformat()
        }


# 싱글톤 인스턴스 생성
finance_api_service = FinanceApiService()
