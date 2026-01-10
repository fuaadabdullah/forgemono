import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';

describe('Jest DOM Test', () => {
  it('should have jest-dom matchers', () => {
    render(<div>Hello World</div>);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });
});
