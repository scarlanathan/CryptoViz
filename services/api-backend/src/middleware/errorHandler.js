const logger = require('../utils/logger');

module.exports = (err, req, res, next) => {
  logger.error('Unhandled error:', err);

  const status = err.status || 500;
  const response = {
    error: err.name || 'InternalServerError',
    message: err.message || 'Something went wrong',
    timestamp: new Date().toISOString(),
    requestId: req.id,
  };

  if (process.env.NODE_ENV !== 'production' && err.stack) {
    response.stack = err.stack;
  }

  res.status(status).json(response);
};
