import { create } from "zustand";

interface UIState {
    // Theme
    theme: "dark" | "light";
    setTheme: (theme: "dark" | "light") => void;
    toggleTheme: () => void;

    // Sidebar
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
    toggleSidebar: () => void;

    // Modals
    orderConfirmModalOpen: boolean;
    setOrderConfirmModalOpen: (open: boolean) => void;

    settingsModalOpen: boolean;
    setSettingsModalOpen: (open: boolean) => void;

    // Notifications
    notifications: Notification[];
    addNotification: (notification: Omit<Notification, "id" | "timestamp">) => void;
    removeNotification: (id: string) => void;
    clearNotifications: () => void;
}

interface Notification {
    id: string;
    type: "success" | "error" | "warning" | "info";
    title: string;
    message?: string;
    timestamp: Date;
}

export const useUIStore = create<UIState>((set) => ({
    // Theme
    theme: "dark",
    setTheme: (theme) => set({ theme }),
    toggleTheme: () =>
        set((state) => ({ theme: state.theme === "dark" ? "light" : "dark" })),

    // Sidebar
    sidebarOpen: true,
    setSidebarOpen: (open) => set({ sidebarOpen: open }),
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    // Modals
    orderConfirmModalOpen: false,
    setOrderConfirmModalOpen: (open) => set({ orderConfirmModalOpen: open }),

    settingsModalOpen: false,
    setSettingsModalOpen: (open) => set({ settingsModalOpen: open }),

    // Notifications
    notifications: [],
    addNotification: (notification) =>
        set((state) => ({
            notifications: [
                ...state.notifications,
                {
                    ...notification,
                    id: crypto.randomUUID(),
                    timestamp: new Date(),
                },
            ],
        })),
    removeNotification: (id) =>
        set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
        })),
    clearNotifications: () => set({ notifications: [] }),
}));
