"""
금융위원회 공개데이터포털 API 호출을 담당하는 서비스 모듈
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class FinanceApiService:
    """금융위원회 공개데이터포털 API 호출 서비스"""
    
    def __init__(self):
        # 공통 베이스 URL
        self.base_url = "http://apis.data.go.kr/1160100/service"
        # 서비스 키 (인증키)
        self.service_key = "4614abeae6a355ee62d9d9ac6ff0799dae33fca08be8939ee0199563ac8e2f61"
        self.timeout = 30.0
    
    async def fetch_disclosure_info(self, page_no: int = 1, num_of_rows: int = 10, bas_dt: Optional[str] = None, auto_retry: bool = True) -> Dict:
        """
        금융위원회 공시정보를 가져옵니다. (명세서: GetDiscInfoService_V2)
        기본적으로 배당공시정보(getDiviDiscInfo_V2)를 호출하도록 설정했습니다.
        
        Args:
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 페이지당 행 수 (기본값: 10)
            bas_dt: 기준일자 (YYYYMMDD 형식, None이면 오늘 날짜 사용)
            auto_retry: 데이터가 없을 경우 이전 날짜로 자동 재시도 (기본값: True, 최대 30일)
        """
        try:
            # 명세서 기준 정확한 경로: 서비스명/상세기능명
            url = f"{self.base_url}/GetDiscInfoService_V2/getDiviDiscInfo_V2"
            
            # 기준일자가 없으면 오늘 날짜를 YYYYMMDD 형식으로 설정
            if bas_dt is None:
                current_date = datetime.now()
            else:
                current_date = datetime.strptime(bas_dt, "%Y%m%d")
            
            # 최대 30일까지 시도 (오늘 포함)
            max_retries = 30
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for day_offset in range(max_retries):
                    # 현재 시도할 날짜 계산
                    target_date = current_date - timedelta(days=day_offset)
                    target_date_str = target_date.strftime("%Y%m%d")
                    
                    params = {
                        "serviceKey": self.service_key,
                        "resultType": "json",
                        "pageNo": page_no,
                        "numOfRows": num_of_rows,
                        "basDt": target_date_str
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()
                    
                    # 응답 구조 확인 및 totalCount 체크
                    total_count = 0
                    try:
                        if "response" in result and "body" in result["response"]:
                            total_count = result["response"]["body"].get("totalCount", 0)
                    except (KeyError, TypeError) as e:
                        print(f"응답 파싱 오류: {e}")
                    
                    # 데이터가 있으면 해당 결과 반환
                    if total_count > 0:
                        if day_offset > 0:
                            print(f"✅ 배당공시정보: {target_date_str} 날짜의 데이터를 조회했습니다. (원래 요청: {current_date.strftime('%Y%m%d')})")
                        else:
                            print(f"✅ 배당공시정보: {target_date_str} 날짜의 데이터를 조회했습니다.")
                        return result
                    
                    # auto_retry가 False이면 첫 번째 시도 결과 반환
                    if not auto_retry:
                        return result
                
                # 30일 내에 데이터를 찾지 못한 경우 마지막 결과 반환
                print(f"⚠️ 배당공시정보: 최근 30일 내 데이터를 찾을 수 없습니다.")
                return result
                
        except httpx.HTTPError as e:
            print(f"공시정보 API 호출 실패: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return {"error": str(e)}
    
    async def fetch_bonus_issuance_info(self, page_no: int = 1, num_of_rows: int = 10, bas_dt: Optional[str] = None, auto_retry: bool = True) -> Dict:
        """
        금융위원회 무상증자 공시정보를 가져옵니다. (명세서: GetDiscInfoService_V2)
        상세기능명: getBonuIssuDiscInfo_V2
        
        Args:
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 페이지당 행 수 (기본값: 10)
            bas_dt: 기준일자 (YYYYMMDD 형식, None이면 오늘 날짜 사용)
            auto_retry: 데이터가 없을 경우 이전 날짜로 자동 재시도 (기본값: True, 최대 30일)
        """
        try:
            url = f"{self.base_url}/GetDiscInfoService_V2/getBonuIssuDiscInfo_V2"
            
            # 기준일자가 없으면 오늘 날짜를 YYYYMMDD 형식으로 설정
            if bas_dt is None:
                current_date = datetime.now()
            else:
                current_date = datetime.strptime(bas_dt, "%Y%m%d")
            
            # 최대 30일까지 시도 (오늘 포함)
            max_retries = 30
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for day_offset in range(max_retries):
                    # 현재 시도할 날짜 계산
                    target_date = current_date - timedelta(days=day_offset)
                    target_date_str = target_date.strftime("%Y%m%d")
                    
                    params = {
                        "serviceKey": self.service_key,
                        "resultType": "json",
                        "pageNo": page_no,
                        "numOfRows": num_of_rows,
                        "basDt": target_date_str
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()
                    
                    # 응답 구조 확인 및 totalCount 체크
                    total_count = 0
                    try:
                        if "response" in result and "body" in result["response"]:
                            total_count = result["response"]["body"].get("totalCount", 0)
                    except (KeyError, TypeError) as e:
                        print(f"응답 파싱 오류: {e}")
                    
                    # 데이터가 있으면 해당 결과 반환
                    if total_count > 0:
                        if day_offset > 0:
                            print(f"✅ 무상증자 공시정보: {target_date_str} 날짜의 데이터를 조회했습니다. (원래 요청: {current_date.strftime('%Y%m%d')})")
                        else:
                            print(f"✅ 무상증자 공시정보: {target_date_str} 날짜의 데이터를 조회했습니다.")
                        return result
                    
                    # auto_retry가 False이면 첫 번째 시도 결과 반환
                    if not auto_retry:
                        return result
                
                # 30일 내에 데이터를 찾지 못한 경우 마지막 결과 반환
                print(f"⚠️ 무상증자 공시정보: 최근 30일 내 데이터를 찾을 수 없습니다.")
                return result
                
        except httpx.HTTPError as e:
            print(f"무상증자 공시정보 API 호출 실패: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return {"error": str(e)}
    
    async def fetch_stock_price_info(self, page_no: int = 1, num_of_rows: int = 10, bas_dt: Optional[str] = None, auto_retry: bool = True) -> Dict:
        """
        금융위원회 주식시세정보를 가져옵니다. (명세서: GetStockSecuritiesInfoService)
        
        Args:
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 페이지당 행 수 (기본값: 10)
            bas_dt: 기준일자 (YYYYMMDD 형식, None이면 오늘 날짜 사용)
            auto_retry: 데이터가 없을 경우 이전 날짜로 자동 재시도 (기본값: True, 최대 8일)
        """
        try:
            # 명세서 기준 정확한 서비스명과 상세기능명
            url = f"{self.base_url}/GetStockSecuritiesInfoService/getStockPriceInfo"
            
            # 기준일자가 없으면 오늘 날짜를 YYYYMMDD 형식으로 설정
            if bas_dt is None:
                current_date = datetime.now()
            else:
                current_date = datetime.strptime(bas_dt, "%Y%m%d")
            
            # 최대 8일까지 시도 (오늘 포함)
            max_retries = 8
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for day_offset in range(max_retries):
                    # 현재 시도할 날짜 계산
                    target_date = current_date - timedelta(days=day_offset)
                    target_date_str = target_date.strftime("%Y%m%d")
                    
                    params = {
                        "serviceKey": self.service_key,
                        "resultType": "json",
                        "pageNo": page_no,
                        "numOfRows": num_of_rows,
                        "basDt": target_date_str
                    }
                    
                    # 실제 호출되는 전체 URL 생성 (디버깅용)
                    full_url = f"{url}?serviceKey={self.service_key}&resultType=json&pageNo={page_no}&numOfRows={num_of_rows}&basDt={target_date_str}"
                    print(f"주식시세정보 API 호출:")
                    print(f"  - 요청 날짜: {target_date_str}")
                    print(f"  - 전체 URL: {full_url}")
                    print(f"  - 파라미터: {params}")
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()
                    
                    # 응답 전체를 로그로 출력 (디버깅용)
                    print(f"  - 응답 상태코드: {response.status_code}")
                    print(f"  - 응답 헤더: {dict(response.headers)}")
                    print(f"  - 응답 본문 (일부): {str(result)[:500]}")
                    
                    # 응답 구조 확인 및 totalCount 체크
                    total_count = 0
                    response_bas_dt = None
                    all_response_dates = []
                    try:
                        if "response" in result and "body" in result["response"]:
                            total_count = result["response"]["body"].get("totalCount", 0)
                            # 응답 데이터의 실제 basDt 확인 (모든 항목 확인)
                            items = result["response"]["body"].get("items", {})
                            if isinstance(items, dict) and "item" in items:
                                item_list = items["item"]
                                if isinstance(item_list, list) and len(item_list) > 0:
                                    # 모든 항목의 날짜 수집
                                    all_response_dates = [item.get("basDt") for item in item_list if item.get("basDt")]
                                    if all_response_dates:
                                        response_bas_dt = max(all_response_dates)  # 가장 최신 날짜
                                elif isinstance(item_list, dict):
                                    response_bas_dt = item_list.get("basDt")
                                    if response_bas_dt:
                                        all_response_dates = [response_bas_dt]
                    except (KeyError, TypeError) as e:
                        print(f"응답 파싱 오류: {e}")
                    
                    # 응답 날짜와 요청 날짜 확인
                    if response_bas_dt:
                        if response_bas_dt != target_date_str:
                            print(f"⚠️ 요청한 날짜({target_date_str})와 응답 데이터의 최신 날짜({response_bas_dt})가 다릅니다.")
                            print(f"   응답 데이터의 날짜들: {sorted(set(all_response_dates), reverse=True)[:5] if all_response_dates else '없음'}")
                            # 응답 날짜가 요청 날짜보다 오래된 경우에만 계속 시도
                            # 응답 날짜가 요청 날짜보다 최신이거나 같으면 반환 (API가 자동으로 최신 데이터를 반환하는 경우)
                            if response_bas_dt < target_date_str:
                                print(f"   응답 날짜가 요청 날짜보다 오래되었습니다. 계속 시도합니다...")
                                continue
                            else:
                                print(f"   응답 날짜가 요청 날짜보다 최신입니다. 해당 데이터를 반환합니다.")
                        else:
                            print(f"✅ 응답 날짜 확인: {response_bas_dt} (요청과 일치)")
                    else:
                        print(f"⚠️ 응답 데이터에 basDt 필드가 없습니다. 데이터가 있으면 반환합니다.")
                    
                    # 데이터가 있으면 해당 결과 반환
                    if total_count > 0:
                        if day_offset > 0:
                            print(f"✅ 주식시세정보: {response_bas_dt or target_date_str} 날짜의 데이터를 조회했습니다. (원래 요청: {current_date.strftime('%Y%m%d')})")
                        else:
                            print(f"✅ 주식시세정보: {response_bas_dt or target_date_str} 날짜의 데이터를 조회했습니다.")
                        return result
                    
                    # auto_retry가 False이면 첫 번째 시도 결과 반환
                    if not auto_retry:
                        return result
                
                # 8일 내에 데이터를 찾지 못한 경우 마지막 결과 반환
                print(f"⚠️ 주식시세정보: 최근 8일 내 데이터를 찾을 수 없습니다. 마지막 응답 날짜: {response_bas_dt}")
                return result
                
        except httpx.HTTPError as e:
            print(f"주식시세정보 API 호출 실패: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return {"error": str(e)}

    async def fetch_stock_issuance_info(self, page_no: int = 1, num_of_rows: int = 10) -> Dict:
        """
        금융위원회 주식발행 공시정보를 가져옵니다. (명세서: GetStkIssuInfoService)
        """
        try:
            # 명세서 기준 정확한 서비스명과 상세기능명 (주식총수현황)
            url = f"{self.base_url}/GetStkIssuInfoService/getStkIssuInfo"
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
    
    async def fetch_all_finance_data(self, page_no: int = 1, num_of_rows: int = 10) -> Dict:
        """
        모든 금융위원회 데이터를 한번에 가져옵니다.
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


class KrxApiService:
    """한국거래소(KRX) API 호출 서비스"""
    
    def __init__(self):
        self.base_url = "https://data-dbg.krx.co.kr/svc/apis"
        self.api_key = "73346D637E1B47AA8B653668D4D969288CEAB195"
        self.timeout = 30.0
    
    async def fetch_kospi_index(self, bas_dd: Optional[str] = None) -> Dict:
        """
        한국거래소 코스피 지수 데이터를 가져옵니다.
        
        Args:
            bas_dd: 기준일자 (YYYYMMDD 형식, None이면 오늘 날짜 사용)
        
        Returns:
            Dict: 코스피 지수 데이터
        """
        try:
            url = f"{self.base_url}/idx/krx_dd_trd"
            
            # 기준일자가 없으면 오늘 날짜를 YYYYMMDD 형식으로 설정
            if bas_dd is None:
                current_date = datetime.now()
                bas_dd = current_date.strftime("%Y%m%d")
            
            # KRX API 표준 방식: 쿼리 파라미터로 AUTH_KEY 전달
            params = {
                "AUTH_KEY": self.api_key,
                "basDd": bas_dd
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                print(f"🔍 코스피 지수 데이터 조회 시도: {bas_dd}")
                print(f"   URL: {url}")
                print(f"   파라미터: basDd={bas_dd}")
                
                response = await client.get(url, headers=headers, params=params)
                
                print(f"   응답 상태: {response.status_code}")
                
                response.raise_for_status()
                result = response.json()
                
                print(f"✅ 코스피 지수 데이터 조회 성공: {bas_dd}")
                print(f"   응답 구조: {list(result.keys()) if isinstance(result, dict) else '배열'}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            print(f"❌ 코스피 지수 API 호출 실패: {e.response.status_code}")
            if e.response.status_code == 401:
                print(f"   인증 오류: API 키가 유효하지 않거나 승인되지 않았습니다.")
            print(f"   응답 본문: {e.response.text[:500]}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except httpx.HTTPError as e:
            print(f"❌ 코스피 지수 API 호출 실패: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return {"error": str(e)}
    
    async def fetch_kosdaq_index(self, bas_dd: Optional[str] = None) -> Dict:
        """
        한국거래소 코스닥 지수 데이터를 가져옵니다.
        
        Args:
            bas_dd: 기준일자 (YYYYMMDD 형식, None이면 오늘 날짜 사용)
        
        Returns:
            Dict: 코스닥 지수 데이터
        """
        try:
            url = f"{self.base_url}/idx/krx_dd_trd"
            
            # 기준일자가 없으면 오늘 날짜를 YYYYMMDD 형식으로 설정
            if bas_dd is None:
                current_date = datetime.now()
                bas_dd = current_date.strftime("%Y%m%d")
            
            # KRX API 표준 방식: 쿼리 파라미터로 AUTH_KEY 전달
            params = {
                "AUTH_KEY": self.api_key,
                "basDd": bas_dd
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                print(f"🔍 코스닥 지수 데이터 조회 시도: {bas_dd}")
                print(f"   URL: {url}")
                print(f"   파라미터: basDd={bas_dd}")
                
                response = await client.get(url, headers=headers, params=params)
                
                print(f"   응답 상태: {response.status_code}")
                
                response.raise_for_status()
                result = response.json()
                
                print(f"✅ 지수 데이터 조회 성공: {bas_dd}")
                print(f"   응답 구조: {list(result.keys()) if isinstance(result, dict) else '배열'}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            print(f"❌ 코스닥 지수 API 호출 실패: {e.response.status_code}")
            if e.response.status_code == 401:
                print(f"   인증 오류: API 키가 유효하지 않거나 승인되지 않았습니다.")
            print(f"   응답 본문: {e.response.text[:500]}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except httpx.HTTPError as e:
            print(f"❌ 코스닥 지수 API 호출 실패: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return {"error": str(e)}


# 싱글톤 인스턴스 생성
finance_api_service = FinanceApiService()
krx_api_service = KrxApiService()