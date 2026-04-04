import { useUIStore } from '../store/uiStore';

describe('UI Store', () => {
  it('should have initial state', () => {
    const state = useUIStore.getState();
    expect(state.selectedView).toBe('world');
    expect(state.zoomLevel).toBe(2);
    expect(state.mapMode).toBe('3D');
  });

  it('should change view', () => {
    const { setView } = useUIStore.getState();
    setView('charts');
    expect(useUIStore.getState().selectedView).toBe('charts');
  });

  it('should toggle map mode', () => {
    const { toggleMapMode } = useUIStore.getState();
    const initialMode = useUIStore.getState().mapMode;
    toggleMapMode();
    expect(useUIStore.getState().mapMode).not.toBe(initialMode);
  });
});
