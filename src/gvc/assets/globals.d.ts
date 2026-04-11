interface Window {
    pywebview: { api: PywebviewApi };
}

interface PywebviewApi {
    get_prefs(): Promise<{ font_size: number }>;
    set_font_size(size: number): Promise<void>;
}
