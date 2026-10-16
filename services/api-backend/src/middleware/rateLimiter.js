const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 分钟
  max: 100,            // 每分钟 100 请求
  standardHeaders: true,
  legacyHeaders: false,
});

module.exports = limiter;
