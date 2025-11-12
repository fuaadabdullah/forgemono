import jwt from 'jsonwebtoken';

export class CapabilityVerifier {
  private secret = 'tool-layer-secret'; // In production, use env var

  verify(token: string): boolean {
    try {
      jwt.verify(token, this.secret);
      return true;
    } catch {
      return false;
    }
  }

  generateToken(payload: any): string {
    return jwt.sign(payload, this.secret, { expiresIn: '1h' });
  }
}