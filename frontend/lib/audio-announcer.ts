// Web Audio API chime synthesizer & Text-to-Speech broadcast helper

class AudioAnnouncer {
  private audioCtx: AudioContext | null = null;
  private voiceEnabled = true;

  constructor() {
    // AudioContext will be initialized on first user interaction
  }

  private getAudioContext(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    if (!this.audioCtx) {
      const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtxClass) {
        this.audioCtx = new AudioCtxClass();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume().catch(() => {});
    }
    return this.audioCtx;
  }

  /**
   * Plays a crisp airport/transit style dual-tone notification chime
   */
  public playChime() {
    try {
      const ctx = this.getAudioContext();
      if (!ctx) return;

      const now = ctx.currentTime;

      // First chime tone (A5 - 880Hz)
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(880, now);
      gain1.gain.setValueAtTime(0, now);
      gain1.gain.linearRampToValueAtTime(0.25, now + 0.04);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.5);

      // Second harmonic chime tone (C#6 - 1108Hz) slightly delayed
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(1108.73, now + 0.18);
      gain2.gain.setValueAtTime(0, now + 0.18);
      gain2.gain.linearRampToValueAtTime(0.3, now + 0.22);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.85);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now + 0.18);
      osc2.stop(now + 0.9);

      // Warm underlying fifth (E6 - 1318Hz) for rich broadcast texture
      const osc3 = ctx.createOscillator();
      const gain3 = ctx.createGain();
      osc3.type = 'triangle';
      osc3.frequency.setValueAtTime(1318.51, now + 0.22);
      gain3.gain.setValueAtTime(0, now + 0.22);
      gain3.gain.linearRampToValueAtTime(0.12, now + 0.26);
      gain3.gain.exponentialRampToValueAtTime(0.001, now + 0.9);
      osc3.connect(gain3);
      gain3.connect(ctx.destination);
      osc3.start(now + 0.22);
      osc3.stop(now + 0.95);
    } catch (e) {
      console.warn('Audio chime failed to play:', e);
    }
  }

  /**
   * Spoken public address announcement via SpeechSynthesis
   */
  public speakToken(tokenNumber: string, farmerName?: string, gate: string = 'Counter 1') {
    if (!this.voiceEnabled || typeof window === 'undefined' || !window.speechSynthesis) return;

    try {
      window.speechSynthesis.cancel(); // Stop any pending speech

      // Space out letters and numbers for natural pronunciation (e.g. "A 0 0 5")
      const spelledToken = tokenNumber.split('').join(' ');
      const message = farmerName
        ? `Attention please. Token ${spelledToken}. ${farmerName}. Please proceed to ${gate}.`
        : `Attention please. Token ${spelledToken}. Please proceed to ${gate}.`;

      const utterance = new SpeechSynthesisUtterance(message);
      utterance.rate = 0.92; // Slightly slower, clear public-address cadence
      utterance.pitch = 1.05;

      // Select natural English voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(
        (v) => v.lang.includes('en-IN') || v.lang.includes('en-GB') || v.lang.includes('en-US')
      );
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      // Delay speech slightly to let the initial chime ring cleanly
      setTimeout(() => {
        window.speechSynthesis.speak(utterance);
      }, 500);
    } catch (e) {
      console.warn('Speech announcement failed:', e);
    }
  }

  /**
   * Broadcast token: chime + speech
   */
  public announceToken(tokenNumber: string, farmerName?: string, gate: string = 'Counter 1') {
    this.playChime();
    this.speakToken(tokenNumber, farmerName, gate);
  }

  public setVoiceEnabled(enabled: boolean) {
    this.voiceEnabled = enabled;
  }

  public isVoiceEnabled(): boolean {
    return this.voiceEnabled;
  }
}

export const announcer = new AudioAnnouncer();
