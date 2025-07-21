from pathlib import Path
from typing import Optional
from time import sleep
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config_manager import ConfigManager
from .logger import setup_logger


class WebAutomator:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = setup_logger(self.__class__.__name__, config.get('general', 'log_level', 'INFO'))
        
        # Chrome 옵션 설정
        options = Options()
        if config.get('web_automation', 'headless'):
            options.add_argument('--headless')
        
        # 성능 최적화 옵션들
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # 이미지 로딩 비활성화로 속도 향상
        options.add_argument('--disable-javascript-harmony-shipping')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-web-security')
        options.add_argument('--metrics-recording-only')
        options.add_argument('--no-first-run')
        options.add_argument('--safebrowsing-disable-auto-update')
        options.add_argument('--enable-automation')
        options.add_argument('--password-store=basic')
        options.add_argument('--use-mock-keychain')
        
        # Selenium 특화 WebGL 차단 (일반 크롬과 동일한 환경 조성)
        options.add_argument('--disable-gpu')  # GPU 완전 비활성화
        options.add_argument('--disable-gpu-sandbox')  # GPU 샌드박스 비활성화
        options.add_argument('--disable-software-rasterizer')  # 소프트웨어 래스터라이저 비활성화
        options.add_argument('--disable-background-timer-throttling')  # 백그라운드 타이머 스로틀링 비활성화
        options.add_argument('--disable-renderer-backgrounding')  # 렌더러 백그라운딩 비활성화
        options.add_argument('--disable-backgrounding-occluded-windows')  # 가려진 윈도우 백그라운딩 비활성화
        options.add_argument('--disable-features=VizDisplayCompositor,VizHitTestSurfaceLayer,TranslateUI')  # Viz 컴포지터 비활성화
        options.add_argument('--force-color-profile=srgb')  # 색상 프로파일 강제 설정
        options.add_argument('--disable-ipc-flooding-protection')  # IPC 플러딩 보호 비활성화
        
        # 메모리 최적화
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        
        # 모바일 브라우저 시뮬레이션 설정
        mobile_emulation = {
            "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        # 추가 모바일 관련 옵션
        options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1')
        
        # Chrome 드라이버 초기화
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(config.get('web_automation', 'implicit_wait', 10))
    

    def login_with_account(self, email: str, password: str):
        """특정 계정으로 로그인"""
        self.logger.info(f'Starting login process for: {email}')
        self.driver.get('https://app.hanlim.world/signin')
        
        # Selenium Chrome 전용 WebGL 차단 (일반 크롬과 차이점 해결)
        try:
            # 페이지 로드 전 스크립트 주입 (Chrome DevTools Protocol 사용)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': """
                // Selenium 환경에서 WebGL 완전 차단
                (function() {
                    console.log('Selenium WebGL blocker initialized');
                    
                    // 모든 WebGL 관련 생성자 제거
                    Object.defineProperty(window, 'WebGLRenderingContext', {
                        get: function() { return undefined; },
                        configurable: false
                    });
                    
                    Object.defineProperty(window, 'WebGL2RenderingContext', {
                        get: function() { return undefined; },
                        configurable: false
                    });
                    
                    // HTMLCanvasElement.getContext 완전 오버라이드
                    const OriginalHTMLCanvasElement = window.HTMLCanvasElement;
                    if (OriginalHTMLCanvasElement) {
                        OriginalHTMLCanvasElement.prototype.getContext = function(contextType, contextAttributes) {
                            console.log('Canvas getContext called:', contextType);
                            if (contextType === 'webgl' || contextType === 'experimental-webgl' || 
                                contextType === 'webgl2' || contextType === 'experimental-webgl2') {
                                console.log('WebGL context blocked in Selenium');
                                return null;
                            }
                            // 2D context는 허용
                            return CanvasRenderingContext2D.prototype.constructor.call(this, contextType, contextAttributes);
                        };
                    }
                    
                    // 전역 에러 핸들러 (더 강력하게)
                    window.addEventListener('error', function(e) {
                        if (e.message && (e.message.includes('WebGL') || e.message.includes('WebGLRenderer'))) {
                            console.log('WebGL error suppressed:', e.message);
                            e.stopPropagation();
                            e.preventDefault();
                            return false;
                        }
                    }, true);
                    
                    // unhandledrejection도 처리
                    window.addEventListener('unhandledrejection', function(e) {
                        if (e.reason && e.reason.message && e.reason.message.includes('WebGL')) {
                            console.log('WebGL promise rejection suppressed:', e.reason.message);
                            e.preventDefault();
                        }
                    });
                })();
                """
            })
            self.logger.info('WebGL blocker injected via CDP')
        except Exception as e:
            self.logger.info(f'CDP injection failed, using fallback: {e}')
            # 폴백: 일반 스크립트 주입
            self.driver.execute_script("""
                window.WebGLRenderingContext = undefined;
                window.WebGL2RenderingContext = undefined;
                HTMLCanvasElement.prototype.getContext = function(type) {
                    if (type.includes('webgl')) return null;
                    return null;
                };
            """)
        
        # 먼저 모달 닫기
        try:
            self.logger.info('Checking for modal to close')
            modal_close_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '._confirmBtn_pmxd4_106'))
            )
            modal_close_button.click()
            self.logger.info('Modal closed')
        except Exception:
            self.logger.info('No modal found or already closed')

        # 아이디 입력
        self.logger.info('Finding email input field')
        email_input = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="email"]'))
        )
        self.logger.info(f'Email input found, entering email: {email}')
        email_input.clear()
        email_input.send_keys(email)
        
        # 비밀번호 입력
        self.logger.info('Finding password input field')
        password_input = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="password"]'))
        )
        self.logger.info('Password input found, entering password')
        password_input.clear()
        password_input.send_keys(password)
        
        # 로그인 버튼 클릭
        self.logger.info('Finding signin button')
        signin_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class*="signin"], .signin-button, button[type="submit"]'))
        )
        self.logger.info('Signin button found, clicking to login')
        
        # JavaScript를 사용하여 안전하게 클릭
        try:
            signin_button.click()
        except Exception as e:
            self.logger.warning(f'Normal click failed: {str(e)}, trying JavaScript click')
            self.driver.execute_script("arguments[0].click();", signin_button)
        
        # 로그인 완료 대기
        self.logger.info('Waiting for login to complete')
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[class*="upload"], .upload-button'))
        )
        self.logger.info(f'Login successful for: {email}')

    # def open_upload_page(self):
    #     """업로드 페이지로 이동 (이미 로그인된 상태에서)"""
    #     self.logger.info('Moving to upload page')
        
    #     # 업로드 버튼 클릭
    #     self.logger.info('Finding upload button')
    #     upload_button = WebDriverWait(self.driver, 10).until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class*="upload"], .upload-button'))
    #     )
    #     self.logger.info('Upload button found, clicking to go to upload page')
        
    #     # JavaScript를 사용하여 안전하게 클릭
    #     try:
    #         upload_button.click()
    #     except Exception as e:
    #         self.logger.warning(f'Normal click failed: {str(e)}, trying JavaScript click')
    #         self.driver.execute_script("arguments[0].click();", upload_button)
        
    #     # 페이지 전환 후 검색창이 나타날 때까지 대기
    #     self.logger.info('Waiting for upload page to fully load with search elements')
    #     WebDriverWait(self.driver, 15).until(
    #         EC.presence_of_element_located((By.CSS_SELECTOR, '.upload-step-1-search-container input'))
    #     )
    #     sleep(2)  # 추가 안정화 대기
    #     self.logger.info('Upload page loaded successfully')
    
    def logout(self):
        """
        ====================================================================
        ⚠️  로그아웃 로직 - 사용자 수정 필요할 수 있는 부분 ⚠️
        ====================================================================
        
        현재 구현된 로그아웃 로직:
        1. 프로필/메뉴 버튼 클릭 시도
        2. 로그아웃 버튼 찾기 및 클릭
        3. 로그아웃 확인
        
        웹사이트 UI가 변경되면 아래 CSS 선택자들을 수정해야 할 수 있습니다:
        - 프로필 버튼: 'button[class*="profile"], .profile-button, .user-menu'
        - 로그아웃 버튼: 'button[class*="logout"], .logout-button, .signout'
        
        ====================================================================
        """
        
        try:
            self.logger.info('🚪 Starting logout process')
            
            # 프로필/메뉴 버튼 클릭 시도
            self.logger.info('🔍 Looking for profile/menu button')
            nav_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'img[alt*="nav-icon-4"]'))
            )
            nav_button.click()
            self.logger.info('👤 Profile menu opened')
            sleep(1)  # 메뉴 로딩 대기
            
            # 프로필 버튼 찾기
            profile_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.account-box'))
            )
            profile_button.click()
            self.logger.info('👤 Profile menu opened')
            sleep(1)  # 메뉴 로딩 대기
            
            if profile_button:
                profile_button.click()
                self.logger.info('👤 Profile menu opened')
                sleep(1)  # 메뉴 로딩 대기
            else:
                self.logger.warning('⚠️ Could not find profile button, trying direct logout')
            
            # 로그아웃 버튼 찾기
            # account__options 중 두번째 요소
            logout_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.account__options:nth-child(2)'))
            )
            logout_button.click()
            self.logger.info('🚪 Logout button clicked')
            sleep(1)  # 메뉴 로딩 대기
                
        except Exception as e:
            self.logger.error(f'❌ Logout failed: {str(e)}')
            # 최후의 수단: 로그인 페이지로 강제 이동
            self.logger.info('🔄 Force logout by navigating to signin page')
            self.driver.get('https://app.hanlim.world/signin')
        
        self.logger.info('🏁 Logout process completed')
        
        """
        ====================================================================
        로그아웃 로직 수정이 필요한 경우:
        
        1. 웹사이트에서 실제 로그아웃 버튼의 CSS 선택자 확인
        2. 위의 profile_selectors와 logout_selectors 배열에 추가
        3. 로그아웃 확인 로직도 필요에 따라 수정
        
        예시:
        profile_selectors.append('.new-profile-selector')
        logout_selectors.append('.new-logout-selector')
        ====================================================================
        """

    def _handle_alert_if_present(self):
        """알림창이 있으면 확인 버튼을 클릭하여 닫기"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.logger.info(f'Alert detected: {alert_text}')
            alert.accept()  # 확인 버튼 클릭
            self.logger.info('Alert accepted and closed')
            sleep(1)  # 알림 처리 후 잠시 대기
        except Exception:
            # 알림이 없으면 그냥 넘어감
            pass

    def _close_file_dialog_if_open(self):
        """파일 선택 다이얼로그가 열려있으면 빠르게 ESC로 닫기"""
        try:
            from selenium.webdriver.common.keys import Keys
            
            self.logger.info('Closing file dialog with ESC key')
            
            # 가장 효과적인 방법: 빠른 ESC 키 전송
            try:
                # 방법 1: 현재 활성 요소에 ESC 전송 (가장 빠름)
                self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                sleep(0.1)  # 최소한의 대기
                
                # 방법 2: body에도 ESC 전송 (보험)
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                sleep(0.1)  # 최소한의 대기
                
                self.logger.info('ESC keys sent to close file dialog')
                
            except Exception as e:
                # ESC가 안 되면 JavaScript로 빠르게 시도
                try:
                    self.driver.execute_script("""
                        // ESC 키 이벤트 직접 발생
                        var escEvent = new KeyboardEvent('keydown', {
                            key: 'Escape',
                            code: 'Escape',
                            keyCode: 27,
                            which: 27,
                            bubbles: true
                        });
                        document.dispatchEvent(escEvent);
                        document.body.dispatchEvent(escEvent);
                    """)
                    self.logger.info('JavaScript ESC event dispatched')
                except Exception:
                    self.logger.debug('File dialog close failed, continuing...')
                    
        except Exception as e:
            self.logger.debug(f'Error closing file dialog: {str(e)}')
            # 에러가 발생해도 계속 진행 (최대 0.2초만 소요)

    def _wait_for_file_upload_completion(self, timeout=3):
        """파일 업로드 완료까지 빠르게 대기"""
        try:
            self.logger.info('Quick check for file upload completion')
            
            # 간단하고 빠른 확인만 수행
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # 다음 버튼이 활성화되었는지만 빠르게 확인
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 
                        '.next-step-button, button.next, button[class*="next"]')
                    if next_button.is_enabled():
                        self.logger.info('Next button enabled - upload completed')
                        return
                except Exception:
                    pass
                
                # 로딩 인디케이터가 없으면 완료로 간주
                try:
                    loading = self.driver.find_elements(By.CSS_SELECTOR, '.loading, .spinner, .uploading')
                    if not loading:
                        self.logger.info('No loading indicators - upload likely completed')
                        return
                except Exception:
                    pass
                
                sleep(0.2)  # 0.2초씩 빠르게 확인
            
            self.logger.info('Upload completion check timeout - proceeding')
            
        except Exception as e:
            self.logger.debug(f'Upload completion check error: {str(e)}')
            # 에러가 발생해도 계속 진행 (최대 3초만 소요)

    def _find_element_safely(self, selector: str, timeout: int = 10, description: str = "", fast_mode: bool = False):
        """Safely find element with retry logic to avoid stale element issues"""
        if fast_mode:
            # 빠른 모드: 요소가 존재하기만 하면 바로 반환 (클릭 가능 여부 무시)
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                self.logger.info(f'Element found (fast){f" ({description})" if description else ""}: {selector}')
                return element
            except Exception as e:
                self.logger.error(f'Failed to find element in fast mode: {selector}')
                raise e
        
        # 일반 모드: 기존 로직
        for attempt in range(3):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.logger.info(f'Element found{f" ({description})" if description else ""}: {selector}')
                return element
            except Exception as e:
                if attempt < 2:
                    self.logger.warning(f'Attempt {attempt + 1} failed for {selector}: {str(e)}, retrying...')
                    sleep(1)
                else:
                    self.logger.error(f'Failed to find element after 3 attempts: {selector}')
                    raise e

    def _click_element_safely(self, element, description: str = ""):
        """Safely click element with JavaScript fallback"""
        try:
            element.click()
            self.logger.info(f'Successfully clicked{f" {description}" if description else ""}')
        except Exception as e:
            self.logger.warning(f'Normal click failed{f" for {description}" if description else ""}: {str(e)}, trying JavaScript click')
            self.driver.execute_script("arguments[0].click();", element)
            self.logger.info(f'JavaScript click successful{f" for {description}" if description else ""}')

    
    def search_song(self, query: str) -> None:
        try:
            # 업로드 버튼 클릭 - 빠른 감지 모드
            self.logger.info('Finding upload button (fast mode)')
            upload_button = self._find_element_safely(
                'button[class*="upload"], .upload-button',
                timeout=8,
                description="upload button",
                fast_mode=True
            )
            self.logger.info('Upload button found, clicking to go to upload page')
            
            # JavaScript를 사용하여 안전하게 클릭 (즉시 클릭)
            self.driver.execute_script("arguments[0].click();", upload_button)
            self.logger.info('Upload button clicked via JavaScript')

            # 페이지 전환 후 검색창이 나타날 때까지 대기
            self.logger.info('Waiting for upload page to fully load with search elements')
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.upload-step-1-search-container input'))
            )
            
            # 검색창이 완전히 로드되고 상호작용 가능할 때까지 대기
            self.logger.info('Step 1: Waiting for search box to be fully interactive')
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.upload-step-1-search-container input'))
            )
            
            # 검색창 요소 찾기 (매번 새로 찾기)
            self.logger.info('Step 1: Finding search box')
            search_box = self._find_element_safely(
                '.upload-step-1-search-container input',
                timeout=10,
                description="search input box"
            )
            
            self.logger.info('Step 1: Search box found, focusing and clearing')
            
            # 검색창이 실제로 클릭 가능한지 확인
            if not search_box.is_enabled():
                self.logger.warning('Search box is not enabled, waiting...')
                sleep(2)
            
            # 검색창에 포커스 주기
            self._click_element_safely(search_box, "search box focus")
            sleep(0.3)  # 포커스 안정화
            
            # 기존 내용 완전히 지우기
            search_box.clear()
            self.driver.execute_script("arguments[0].value = '';", search_box)
            sleep(0.3)  # 클리어 안정화
            
            self.logger.info(f'Step 1: Entering search query: {query}')
            
            # 텍스트 입력 시도
            for attempt in range(3):
                try:
                    # 검색창 다시 찾기 (stale element 방지)
                    search_box = self._find_element_safely(
                        '.upload-step-1-search-container input',
                        timeout=5,
                        description="search input box (retry)"
                    )
                    
                    # 입력 전 포커스 확인
                    self._click_element_safely(search_box, "search box refocus")
                    sleep(0.3)
                    
                    # 입력 시도
                    search_box.send_keys(query)
                    sleep(0.5)
                    
                    # 값이 제대로 입력되었는지 확인
                    current_value = search_box.get_attribute('value')
                    self.logger.info(f'Step 1: Current input value: "{current_value}"')
                    
                    if current_value == query:
                        self.logger.info('Step 1: Query entered successfully')
                        break
                    elif attempt < 2:
                        self.logger.warning(f'Input value mismatch (attempt {attempt + 1}). Expected: "{query}", Got: "{current_value}". Retrying...')
                        # 다시 지우고 시도
                        search_box.clear()
                        self.driver.execute_script("arguments[0].value = '';", search_box)
                        sleep(0.5)
                    else:
                        self.logger.warning(f'Final attempt: Using JavaScript to set value')
                        # JavaScript로 강제 입력
                        self.driver.execute_script(f"arguments[0].value = '{query}';", search_box)
                        # 이벤트 발생
                        self.driver.execute_script("""
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        """, search_box)
                        
                        # 최종 확인
                        current_value = search_box.get_attribute('value')
                        self.logger.info(f'Step 1: Final value after JavaScript: "{current_value}"')
                        
                except Exception as e:
                    if attempt < 2:
                        self.logger.warning(f'Input attempt {attempt + 1} failed: {str(e)}, retrying...')
                        sleep(1)
                    else:
                        raise e

            # 검색 버튼 찾기 및 클릭 (매번 새로 찾기)
            self.logger.info('Step 1: Finding search button')
            search_button = self._find_element_safely(
                'img[alt*="검색"]',
                description="search button"
            )
            self._click_element_safely(search_button, "search button")

            self.logger.info('Step 1: Waiting for search results to appear')
            
            # 검색 결과 대기 및 클릭 (매번 새로 찾기)
            self.logger.info('Step 1: Finding search results')
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.search-result-item'))
            )
            
            # 검색 결과 클릭 (매번 새로 찾기)
            result = self._find_element_safely(
                '.search-result-item',
                timeout=5,
                description="search result item"
            )
            self._click_element_safely(result, "search result")
                
            self.logger.info('Step 1: Song search completed successfully')
            
        except Exception as e:
            self.logger.error(f'Error during song search: {str(e)}')
            # JavaScript로 페이지 내용 확인
            page_content = self.driver.execute_script("""
            return {
                body: document.body.innerHTML.substring(0, 1000),
                searchBox: document.querySelector('.upload-step-1-search-container input') ? 'found' : 'not found',
                searchValue: document.querySelector('.upload-step-1-search-container input')?.value || 'no value'
            };
            """)
            self.logger.info(f'Page debug info: {page_content}')
            raise

    def upload_video(self, file_path: Path, artist: str, title: str, description: str, tracker=None) -> bool:
        try:
            # 검색 쿼리 생성 (artist가 빈 문자열이면 title만 사용)
            if artist and artist.strip():
                search_query = f"{artist} {title}"
            else:
                search_query = title
                
            self.logger.info(f'Starting upload process for: {file_path.name}')
            self.logger.info(f'Search query: {search_query}')
            
            # ThreeJS 호환 WebGL 오류 방지 재주입
            try:
                threejs_compat_script = """
                (function() {
                    const originalGetContext = HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext = function(contextType, contextAttributes) {
                        if (contextType === 'webgl' || contextType === 'experimental-webgl' || 
                            contextType === 'webgl2' || contextType === 'experimental-webgl2') {
                            return null;
                        }
                        return originalGetContext.call(this, contextType, contextAttributes);
                    };
                    
                    // 전역 오류 처리기
                    window.addEventListener('error', function(e) {
                        if (e.message && e.message.includes('WebGL')) {
                            e.preventDefault();
                            return false;
                        }
                    });
                    
                    // ThreeJS WebGLRenderer 폴백
                    if (window.THREE && window.THREE.WebGLRenderer) {
                        window.THREE.WebGLRenderer = function() {
                            return {
                                domElement: document.createElement('div'),
                                setSize: function() {},
                                render: function() {},
                                dispose: function() {}
                            };
                        };
                    }
                })();
                """
                self.driver.execute_script(threejs_compat_script)
            except Exception:
                pass  # 실패해도 계속 진행
            
            # 업로드 시작 전에 알림창 처리
            self._handle_alert_if_present()
            
            # # Step 1: Navigate to upload page first
            # self.open_upload_page()
            
            # Step 2: Search for song
            self.search_song(search_query)
            
            # Step 3: Scroll down to reveal next button and click
            self.logger.info('Step 3: Scrolling down to reveal next button')
            
            # 페이지 끝까지 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)  # 스크롤 완료 대기
            
            self.logger.info('Step 3: Finding next button to proceed')
            next_btn = self._find_element_safely(
                '.next-step-button, button.next, button[class*="next"]',
                description="next button"
            )
            
            # 버튼이 화면에 보이도록 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_btn)
            sleep(1)  # 스크롤 완료 대기
            
            self.logger.info('Step 3: Next button found and scrolled into view, clicking to proceed')
            self._click_element_safely(next_btn, "next button")
            
            # Step 4: Click import/gallery button
            self.logger.info('Step 4: Finding gallery/import button')
            import_btn = self._find_element_safely(
                '.gallery-banner, button.import, button[class*="import"], button[class*="gallery"]',
                description="gallery/import button"
            )
            self._click_element_safely(import_btn, "gallery button")
            self.logger.info('Step 4: File dialog opened')
            
            # Step 5: Upload file
            self.logger.info('Step 5: Finding file input element')
            file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
            )
            self.logger.info(f'Step 5: File input found, uploading file: {file_path.resolve()}')
            file_input.send_keys(str(file_path.resolve()))
            self.logger.info('Step 5: File upload initiated')
            
            # 파일 선택 후 빠른 처리
            sleep(0.3)  # 최소한의 파일 선택 처리 대기
            self._close_file_dialog_if_open()
            self._wait_for_file_upload_completion()
            
            # Step 6: Click next to proceed to description
            self.logger.info('Step 6: Finding next button after file upload')
            next_btn = self._find_element_safely(
                '.next-step-button, button.next, button[class*="next"]',
                description="next button after upload"
            )
            self._click_element_safely(next_btn, "next button after upload")
            self.logger.info('Step 6: Moved to description step')
            
            # Step 7: Enter description
            self.logger.info('Step 7: Finding description textarea')
            desc_area = self._find_element_safely(
                'textarea.description, textarea[class*="description"], textarea',
                description="description textarea"
            )
            self.logger.info(f'Step 7: Description area found, entering text: {description}')
            desc_area.send_keys(description)
            self.logger.info('Step 7: Description entered')
            
            # Step 8: Final upload
            self.logger.info('Step 8: Finding final upload button')
            upload_btn = self._find_element_safely(
                '.next-step-button, button.submit, button[class*="submit"], button[class*="upload"]',
                description="final upload button"
            )
            self._click_element_safely(upload_btn, "final upload button")
            self.logger.info(f'Step 8: Upload completed successfully for {file_path.name}')
            
            # 업로드 성공 시 트래커에 기록
            if tracker:
                tracker.mark_as_uploaded(file_path.name, artist, title)
                self.logger.info(f'Recorded upload success in tracker for: {file_path.name}')
            
            return True
        
        except Exception as e:
            self.logger.error(f'Upload failed for {file_path.name}: {str(e)}')
            
            # 업로드 실패 시 복구 시도
            try:
                self.logger.info('🔄 Attempting recovery: clicking new-bottom-nav first child div')
                
                # new-bottom-nav의 첫 번째 하위 div 클릭 (nth-child 문법 사용)
                nav_first_child = self._find_element_safely(
                    '.new-bottom-nav > div:nth-child(1), .new-bottom-nav div:nth-child(1), .new-bottom-nav > *:nth-child(1), .new-bottom-nav *:nth-child(1)',
                    description="new-bottom-nav first child element"
                )
                if nav_first_child:
                    self._click_element_safely(nav_first_child, "new-bottom-nav first child")
                    sleep(1)  # 네비게이션 완료 대기
                    
                    # search_song 다시 실행
                    self.logger.info('🔄 Retrying search_song function')
                    search_query = f"{artist} {title}" if artist and artist.strip() else title
                    self.search_song(search_query)
                    
                    # 복구 후 다시 업로드 시도
                    self.logger.info('🔄 Retrying upload after recovery')
                    return self._retry_upload_after_recovery(file_path, artist, title, description, tracker)
                    
            except Exception as recovery_error:
                self.logger.error(f'🔄 Recovery attempt failed: {str(recovery_error)}')
            
            return False

    def _retry_upload_after_recovery(self, file_path: Path, artist: str, title: str, description: str, tracker=None) -> bool:
        """복구 후 업로드 재시도"""
        try:
            # Step 3: Scroll down to reveal next button and click
            self.logger.info('Recovery Step 3: Scrolling down to reveal next button')
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)
            
            next_btn = self._find_element_safely(
                '.next-step-button, button.next, button[class*="next"]',
                description="next button"
            )
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_btn)
            sleep(1)
            self._click_element_safely(next_btn, "next button")
            
            # Step 4: Click import/gallery button
            self.logger.info('Recovery Step 4: Finding gallery/import button')
            import_btn = self._find_element_safely(
                '.gallery-banner, button.import, button[class*="import"], button[class*="gallery"]',
                description="gallery/import button"
            )
            self._click_element_safely(import_btn, "gallery button")
            
            # Step 5: Upload file
            self.logger.info('Recovery Step 5: Finding file input element')
            file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
            )
            file_input.send_keys(str(file_path.resolve()))
            
            sleep(0.3)
            self._close_file_dialog_if_open()
            self._wait_for_file_upload_completion()
            
            # Step 6: Click next to proceed to description
            self.logger.info('Recovery Step 6: Finding next button after file upload')
            next_btn = self._find_element_safely(
                '.next-step-button, button.next, button[class*="next"]',
                description="next button after upload"
            )
            self._click_element_safely(next_btn, "next button after upload")
            
            # Step 7: Enter description
            self.logger.info('Recovery Step 7: Finding description textarea')
            desc_area = self._find_element_safely(
                'textarea.description, textarea[class*="description"], textarea',
                description="description textarea"
            )
            desc_area.send_keys(description)
            
            # Step 8: Final upload
            self.logger.info('Recovery Step 8: Finding final upload button')
            upload_btn = self._find_element_safely(
                '.next-step-button, button.submit, button[class*="submit"], button[class*="upload"]',
                description="final upload button"
            )
            self._click_element_safely(upload_btn, "final upload button")
            self.logger.info(f'Recovery Step 8: Upload completed successfully for {file_path.name}')
            
            # 업로드 성공 시 트래커에 기록
            if tracker:
                tracker.mark_as_uploaded(file_path.name, artist, title)
                self.logger.info(f'Recorded recovery upload success in tracker for: {file_path.name}')
            
            return True
            
        except Exception as e:
            self.logger.error(f'Recovery upload failed for {file_path.name}: {str(e)}')
            return False

    def close(self):
        self.logger.info('Closing browser and cleaning up resources')
        self.driver.quit()
        self.logger.info('Browser closed successfully')
