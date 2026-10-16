const isProd = process.env.NODE_ENV === 'production';

const log = (level, ...args) => {
  const ts = new Date().toISOString();
  console[level](`[${ts}] [${level.toUpperCase()}]`, ...args);
};

module.exports = {
  info: (...args) => log('log', ...args),
  warn: (...args) => log('warn', ...args),
  error: (...args) => log('error', ...args),
};
