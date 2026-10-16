const io = require('socket.io-client');

const socket = io('http://localhost:3002', {
    transports: ['websocket'],
});

socket.on('connect', () => {
    console.log('✅ Connected to WebSocket, id =', socket.id);

    socket.emit('subscribe_market_data', {
        symbol: 'BTC/USDT',
        exchange: 'okx',
    });
});

socket.on('market_data_update', (payload) => {
    console.log('📈 Market data update:');
    console.dir(payload, { depth: null });
});

socket.on('connect_error', (err) => {
    console.error('❌ Connect error:', err);
});

socket.on('disconnect', (reason) => {
    console.log('❌ Disconnected:', reason);
});
