import { render, screen } from '@testing-library/react';
import React from 'react';

describe('Basic Application Setup', () => {
  test('jest and react-testing-library are configured', () => {
    render(<div>SatTrade Terminal</div>);
    const element = screen.getByText(/SatTrade Terminal/i);
    expect(element).toBeInTheDocument();
  });
});
