declare global {
  interface Window {
    _env_: {
      [key: string]: string;
    };
  }
}

export {};
