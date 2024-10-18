const env: { [key: string]: string } = {};

if (window && window._env_) {
  Object.keys(window._env_).forEach((key) => {
    env[key] = window._env_[key];
  });
}

export default env;
