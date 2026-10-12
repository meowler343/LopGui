import ctypes
import sys
import time

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

user32.DefWindowProcW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
user32.DefWindowProcW.restype = ctypes.c_longlong
user32.FillRect.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
user32.FillRect.restype = ctypes.c_int

gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
gdi32.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = ctypes.c_void_p
gdi32.BitBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
gdi32.BitBlt.restype = ctypes.c_int

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p)

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.c_void_p),
        ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", ctypes.c_wchar_p),
        ("lpszClassName", ctypes.c_wchar_p),
        ("hIconSm", ctypes.c_void_p),
    ]

class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", ctypes.c_void_p),
        ("fErase", ctypes.c_int),
        ("rcPaint", ctypes.c_long * 4),
        ("fRestore", ctypes.c_int),
        ("fIncUpdate", ctypes.c_int),
        ("rgbReserved", ctypes.c_byte * 32),
    ]

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_void_p),
        ("lParam", ctypes.c_void_p),
        ("time", ctypes.c_ulong),
        ("pt", POINT),
    ]

WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000

WM_PAINT = 0x000F
WM_DESTROY = 0x0002
WM_ERASEBKGND = 0x0014
WM_SIZE = 0x0005
WM_LBUTTONDOWN = 0x0201
WM_MOUSEMOVE = 0x0200

class Button:
    def __init__(self, master, text=".Click me!", font="skandi", style="minimal-black", command=None):
        self.text = text
        self.command = command
        self.width = 280
        self.height = 70
        self.update_position(master.width, master.height)
        self.is_hovered = False

    def update_position(self, parent_width, parent_height):
        self.x = (parent_width - self.width) // 2
        self.y = (parent_height - self.height) // 2

    def contains(self, x, y):
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def draw(self, hdc):
        # Эмуляция красивой тени кнопки
        shadow_brush = gdi32.CreateSolidBrush(0x101015)
        shadow_rect = RECT(self.x + 4, self.y + 6, self.x + self.width + 4, self.y + self.height + 6)
        gdi32.SelectObject(hdc, shadow_brush)
        gdi32.SelectObject(hdc, gdi32.GetStockObject(5)) # NULL_PEN
        gdi32.RoundRect(hdc, shadow_rect.left, shadow_rect.top, shadow_rect.right, shadow_rect.bottom, 18, 18)
        gdi32.DeleteObject(shadow_brush)

        # Тело кнопки (градиентный/стильный темный цвет с фиолетовым акцентом при наведении)
        btn_bg = 0x1E1E2E if self.is_hovered else 0x15151D
        hbrush = gdi32.CreateSolidBrush(btn_bg)
        
        # Рамка с фиолетовым акцентом LopGui при наведении
        border_color = 0xFF26B0 if self.is_hovered else 0x333344
        hpen = gdi32.CreatePen(0, 2, border_color)
        
        gdi32.SelectObject(hdc, hbrush)
        gdi32.SelectObject(hdc, hpen)
        gdi32.RoundRect(hdc, self.x, self.y, self.x + self.width, self.y + self.height, 16, 16)
        
        gdi32.DeleteObject(hbrush)
        gdi32.DeleteObject(hpen)

        # Текст кнопки (белый, современный шрифтовой стиль)
        gdi32.SetTextColor(hdc, 0xFFFFFF)
        gdi32.SetBkMode(hdc, 1)
        
        rect = RECT(self.x, self.y, self.x + self.width, self.y + self.height)
        hfont = gdi32.CreateFontW(20, 0, 0, 0, 600, False, False, False, 1, 0, 0, 2, 0, "Segoe UI")
        old_font = gdi32.SelectObject(hdc, hfont)
        
        user32.DrawTextW(hdc, self.text, len(self.text), ctypes.byref(rect), 0x00000020 | 0x00000001)
        
        gdi32.SelectObject(hdc, old_font)
        gdi32.DeleteObject(hfont)

class App:
    def __init__(self, title="Test", theme="lopgui-dark-purple", width=800, height=500):
        self.title = title
        self.width = width
        self.height = height
        self.components = []
        self.running = True
        self.mouse_x = 0
        self.mouse_y = 0
        
        self._close_hover = False
        self._max_hover = False
        self._min_hover = False
        
        self.class_name = "LopGuiNativeWindow"
        self.hinstance = kernel32.GetModuleHandleW(None)
        
        @WNDPROC
        def wnd_proc(hwnd, msg, wparam, lparam):
            try:
                if msg == WM_ERASEBKGND:
                    return 1
                    
                elif msg == WM_SIZE:
                    self.width = lparam & 0xFFFF
                    self.height = (lparam >> 16) & 0xFFFF
                    for comp in self.components:
                        if hasattr(comp, "update_position"):
                            comp.update_position(self.width, self.height)
                    user32.InvalidateRect(hwnd, None, False)
                    return 0
                    
                elif msg == WM_PAINT:
                    ps = PAINTSTRUCT()
                    hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
                    
                    mem_dc = gdi32.CreateCompatibleDC(hdc)
                    h_bmp = gdi32.CreateCompatibleBitmap(hdc, self.width, self.height)
                    old_bmp = gdi32.SelectObject(mem_dc, h_bmp)
                    
                    # 1. Супер красивый современный фон (Глубокий темный стиль Discord/VS Code)
                    bg_brush = gdi32.CreateSolidBrush(0x13131A)
                    client_rect = RECT(0, 0, self.width, self.height)
                    user32.FillRect(mem_dc, ctypes.byref(client_rect), bg_brush)
                    gdi32.DeleteObject(bg_brush)
                    
                    # 2. Стильная темная шапка окна
                    tb_brush = gdi32.CreateSolidBrush(0x0D0D12)
                    tb_rect = RECT(0, 0, self.width, 38)
                    user32.FillRect(mem_dc, ctypes.byref(tb_rect), tb_brush)
                    gdi32.DeleteObject(tb_brush)
                    
                    # Заголовок окна
                    gdi32.SetTextColor(mem_dc, 0xCCCCCC)
                    gdi32.SetBkMode(mem_dc, 1)
                    title_font = gdi32.CreateFontW(14, 0, 0, 0, 600, False, False, False, 1, 0, 0, 2, 0, "Segoe UI")
                    old_font = gdi32.SelectObject(mem_dc, title_font)
                    
                    title_rect = RECT(16, 10, 300, 38)
                    user32.DrawTextW(mem_dc, self.title, len(self.title), ctypes.byref(title_rect), 0)
                    
                    # 3. Кнопки управления (с фирменным фиолетовым акцентом LopGui #b026ff)
                    close_rect = RECT(self.width - 48, 0, self.width, 38)
                    max_rect = RECT(self.width - 96, 0, self.width - 48, 38)
                    min_rect = RECT(self.width - 144, 0, self.width - 96, 38)
                    
                    close_bg = 0x2311E8 if self._close_hover else 0xFF26B0
                    max_bg = 0x4420CC if self._max_hover else 0xFF26B0
                    min_bg = 0x4420CC if self._min_hover else 0xFF26B0
                    
                    h_close_brush = gdi32.CreateSolidBrush(close_bg)
                    h_max_brush = gdi32.CreateSolidBrush(max_bg)
                    h_min_brush = gdi32.CreateSolidBrush(min_bg)
                    
                    user32.FillRect(mem_dc, ctypes.byref(close_rect), h_close_brush)
                    user32.FillRect(mem_dc, ctypes.byref(max_rect), h_max_brush)
                    user32.FillRect(mem_dc, ctypes.byref(min_rect), h_min_brush)
                    
                    gdi32.DeleteObject(h_close_brush)
                    gdi32.DeleteObject(h_max_brush)
                    gdi32.DeleteObject(h_min_brush)
                    
                    user32.DrawTextW(mem_dc, "—", 1, ctypes.byref(min_rect), 0x00000020 | 0x00000001)
                    user32.DrawTextW(mem_dc, "✕", 1, ctypes.byref(close_rect), 0x00000020 | 0x00000001)
                    
                    h_pen_icon = gdi32.CreatePen(0, 1, 0xFFFFFF)
                    gdi32.SelectObject(mem_dc, h_pen_icon)
                    gdi32.SelectObject(mem_dc, gdi32.GetStockObject(5))
                    
                    mx_cx = (max_rect.left + max_rect.right) // 2
                    mx_cy = (max_rect.top + max_rect.bottom) // 2
                    gdi32.Rectangle(mem_dc, mx_cx - 5, mx_cy - 5, mx_cx + 5, mx_cy + 5)
                    gdi32.DeleteObject(h_pen_icon)

                    gdi32.SelectObject(mem_dc, old_font)
                    gdi32.DeleteObject(title_font)

                    # 4. Отрисовка компонентов
                    for comp in self.components:
                        comp.draw(mem_dc)
                    
                    gdi32.BitBlt(hdc, 0, 0, self.width, self.height, mem_dc, 0, 0, 0x00CC0020)
                    
                    gdi32.SelectObject(mem_dc, old_bmp)
                    gdi32.DeleteObject(h_bmp)
                    gdi32.DeleteObject(mem_dc)
                    
                    user32.EndPaint(hwnd, ctypes.byref(ps))
                    return 0
                    
                elif msg == WM_LBUTTONDOWN:
                    x = lparam & 0xFFFF
                    y = (lparam >> 16) & 0xFFFF
                    if y <= 38:
                        if x >= self.width - 48:
                            self.running = False
                            user32.PostQuitMessage(0)
                        elif self.width - 96 <= x < self.width - 48:
                            if user32.IsZoomed(hwnd):
                                user32.ShowWindow(hwnd, 9)
                            else:
                                user32.ShowWindow(hwnd, 3)
                        elif self.width - 144 <= x < self.width - 96:
                            user32.ShowWindow(hwnd, 6)
                        else:
                            user32.SendMessageW(hwnd, 0x00A1, 2, 0)
                    else:
                        for comp in self.components:
                            if comp.contains(x, y) and comp.command:
                                comp.command()
                    user32.InvalidateRect(hwnd, None, False)
                    return 0
                    
                elif msg == WM_MOUSEMOVE:
                    new_x = lparam & 0xFFFF
                    new_y = (lparam >> 16) & 0xFFFF
                    
                    redraw_needed = False
                    
                    for comp in self.components:
                        old = comp.is_hovered
                        comp.is_hovered = comp.contains(new_x, new_y)
                        if old != comp.is_hovered:
                            redraw_needed = True
                    
                    c_hover = (new_y <= 38 and new_x >= self.width - 48)
                    m_hover = (new_y <= 38 and self.width - 96 <= new_x < self.width - 48)
                    mi_hover = (new_y <= 38 and self.width - 144 <= new_x < self.width - 96)
                    
                    if c_hover != self._close_hover or m_hover != self._max_hover or mi_hover != self._min_hover:
                        self._close_hover = c_hover
                        self._max_hover = m_hover
                        self._min_hover = mi_hover
                        redraw_needed = True
                    
                    self.mouse_x = new_x
                    self.mouse_y = new_y
                    
                    if redraw_needed:
                        user32.InvalidateRect(hwnd, None, False)
                    return 0
                    
                elif msg == WM_DESTROY:
                    self.running = False
                    user32.PostQuitMessage(0)
                    return 0
            except Exception:
                pass
                
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wnd_proc = wnd_proc
        
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = 0x0001 | 0x0002
        wc.lpfnWndProc = self._wnd_proc
        wc.hInstance = self.hinstance
        wc.lpszClassName = self.class_name
        wc.hCursor = user32.LoadCursorW(0, 32512)
        wc.hbrBackground = 0
        user32.RegisterClassExW(ctypes.byref(wc))
        
        style = WS_POPUP | WS_VISIBLE | WS_THICKFRAME | WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
        
        self.hwnd = user32.CreateWindowExW(
            0, self.class_name, self.title,
            style,
            300, 200, self.width, self.height,
            0, 0, self.hinstance, 0
        )
        
        user32.ShowWindow(self.hwnd, 1)
        user32.UpdateWindow(self.hwnd)

    def add(self, component):
        self.components.append(component)

    def run(self):
        msg = MSG()
        while self.running:
            while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
                if msg.message == 0x0012:
                    self.running = False
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.01)