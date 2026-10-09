import { Component, type ReactNode } from 'react'

/** A model that fails to load must never take the page down: the DOM words and lists stay. */
export default class Guard extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    return this.state.failed ? null : this.props.children
  }
}

/**
 * One fixed transparent canvas over the B1/B2 sections (DOM giant words sit underneath, Zoi layering).
 * three/R3F is a lazy chunk, mounted when B1 is ≤ 1 viewport away and unmounted ≥ 2 viewports past B2.
 */
