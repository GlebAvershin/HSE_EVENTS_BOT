"""Базовый класс для парсеров SPA-сайтов через Playwright."""
import asyncio
from typing import List, Optional

from src.parsers.base import BaseParser, EventData


class BrowserParser(BaseParser):
    """
    Базовый класс для парсеров, требующих headless-браузер.
    Использует Playwright для рендеринга JavaScript.
    
    Подклассы должны реализовать метод parse_page(page) -> List[EventData].
    """
    
    # Таймаут ожидания загрузки страницы (мс)
    PAGE_LOAD_TIMEOUT = 30000
    
    # Таймаут ожидания сетевой активности (мс)
    NETWORK_IDLE_TIMEOUT = 15000
    
    def __init__(self, source_name: str, source_url: str):
        super().__init__(source_name, source_url)
        self._browser = None
        self._playwright = None
    
    async def __aenter__(self):
        """Запустить браузер."""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-blink-features=AutomationControlled",
                ]
            )
        except ImportError:
            print(f"  [SKIP] {self.source_name}: playwright not installed")
            self._browser = None
        except Exception as e:
            print(f"  [SKIP] {self.source_name}: browser launch failed: {type(e).__name__}: {e}")
            self._browser = None
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрыть браузер."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def fetch_rendered_html(self, url: str, wait_selector: Optional[str] = None) -> str:
        """
        Загрузить страницу с рендерингом JavaScript.
        
        Args:
            url: URL страницы
            wait_selector: CSS-селектор, появление которого означает загрузку контента
            
        Returns:
            Отрендеренный HTML
        """
        if not self._browser:
            raise RuntimeError("Browser not initialized")
        
        page = await self._browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        
        try:
            # Скрываем признаки автоматизации
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            await page.goto(url, timeout=self.PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
            
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=self.NETWORK_IDLE_TIMEOUT)
                except Exception:
                    # Если селектор не появился — ждём networkidle
                    await page.wait_for_load_state("networkidle", timeout=self.NETWORK_IDLE_TIMEOUT)
            else:
                # Ждём пока сеть успокоится
                await page.wait_for_load_state("networkidle", timeout=self.NETWORK_IDLE_TIMEOUT)
            
            # Небольшая пауза для финального рендеринга
            await asyncio.sleep(1)
            
            html = await page.content()
            return html
        finally:
            await page.close()
    
    async def parse(self) -> List[EventData]:
        """Парсить события через headless-браузер."""
        if not self._browser:
            print(f"  [SKIP] {self.source_name}: browser not available")
            return []
        
        try:
            return await self._parse_with_browser()
        except asyncio.CancelledError:
            # Не пробрасываем CancelledError — это прерывает весь scheduler
            print(f"  [SKIP] {self.source_name}: parsing was cancelled (timeout)")
            return []
        except Exception as e:
            print(f"  [ERROR] {self.source_name}: {type(e).__name__}: {str(e)[:100]}")
            return []
    
    async def _parse_with_browser(self) -> List[EventData]:
        """Реализация парсинга — переопределяется в подклассах."""
        raise NotImplementedError("Subclasses must implement _parse_with_browser()")
