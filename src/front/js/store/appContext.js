import { createContext, useContext, useRef, useState } from "react";
import getState from "./flux";

export const Context = createContext(null);

// Provider holding { store, actions }. getStore() always sees the latest store.
export function AppProvider({ children }) {
  const ref = useRef(null);
  const [state, setState] = useState(() => {
    const initial = getState({
      getStore: () => ref.current.store,
      getActions: () => ref.current.actions,
      setStore: (updates) => {
        ref.current = { ...ref.current, store: { ...ref.current.store, ...updates } };
        setState(ref.current);
      },
    });
    ref.current = initial;
    return initial;
  });
  return <Context.Provider value={state}>{children}</Context.Provider>;
}

export function useStore() {
  return useContext(Context);
}

// 4Geeks-style HOC, for parity with the boilerplate.
const injectContext = (Component) => (props) => (
  <AppProvider>
    <Component {...props} />
  </AppProvider>
);
export default injectContext;
