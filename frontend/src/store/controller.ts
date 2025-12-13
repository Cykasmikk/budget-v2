import { ReactiveController, ReactiveControllerHost } from 'lit';
import { Store } from '@tanstack/store';

export class StoreController<TState> implements ReactiveController {
    host: ReactiveControllerHost;
    store: Store<TState>;
    unsubscribe: () => void = () => { };

    constructor(host: ReactiveControllerHost, store: Store<TState>) {
        (this.host = host).addController(this);
        this.store = store;
    }

    hostConnected() {
        this.unsubscribe = this.store.subscribe(() => {
            this.host.requestUpdate();
        });
    }

    hostDisconnected() {
        this.unsubscribe();
    }
}
