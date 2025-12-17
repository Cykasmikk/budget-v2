import { Store } from '@tanstack/store';

export interface UIState {
    activeTab: string;
}

const initialState: UIState = {
    activeTab: 'dashboard'
};

export class UIStore extends Store<UIState> {
    constructor() {
        super(initialState);
    }

    setActiveTab(tab: string) {
        this.setState((state) => ({
            ...state,
            activeTab: tab
        }));
    }

    reset() {
        this.setState(() => initialState);
    }
}

export const uiStore = new UIStore();
