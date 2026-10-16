#!/bin/bash
# Script pour visualiser les données CRYPTO VIZ

echo "============================================================"
echo "  🚀 CRYPTO VIZ - Visualisation des données"
echo "============================================================"

echo -e "\n📊 STATUS DU DATA PROCESSOR"
echo "------------------------------------------------------------"
curl -s http://localhost:8002/status | python -m json.tool

echo -e "\n\n🔄 STATUS DU DATA COLLECTOR"
echo "------------------------------------------------------------"
curl -s http://localhost:8001/status | python -m json.tool

echo -e "\n\n💾 DONNÉES MONGODB"
echo "------------------------------------------------------------"
echo "Collections et nombre de documents:"
docker exec crypto-mongodb mongosh -u cryptovizuser -p cryptovizpass --authenticationDatabase admin cryptoviz --quiet --eval "
print('  - processed_data: ' + db.processed_data.countDocuments());
print('  - analytics: ' + db.analytics.countDocuments());
print('  - alerts: ' + db.alerts.countDocuments());
"

echo -e "\n📈 PRIX ACTUELS:"
docker exec crypto-mongodb mongosh -u cryptovizuser -p cryptovizpass --authenticationDatabase admin cryptoviz --quiet --eval "
db.processed_data.aggregate([
  {\$sort: {timestamp: -1}},
  {\$group: {
    _id: '\$symbol',
    latest_price: {\$first: '\$raw_data.close'},
    exchange: {\$first: '\$raw_data.exchange'},
    timestamp: {\$first: '\$timestamp'}
  }},
  {\$sort: {_id: 1}}
]).forEach(doc => {
  print('  ' + doc._id.padEnd(12) + doc.latest_price.toFixed(2).padStart(12) + ' USD  (' + doc.exchange + ')');
});
"

echo -e "\n⚠️  DERNIÈRES ALERTES (5 plus récentes):"
docker exec crypto-mongodb mongosh -u cryptovizuser -p cryptovizpass --authenticationDatabase admin cryptoviz --quiet --eval "
db.alerts.find().sort({timestamp: -1}).limit(5).forEach(alert => {
  print('  ' + alert.symbol.padEnd(12) + alert.alert_type.padEnd(20) + ' - ' + alert.message);
});
"

echo -e "\n📊 STATISTIQUES PAR SYMBOLE:"
docker exec crypto-mongodb mongosh -u cryptovizuser -p cryptovizpass --authenticationDatabase admin cryptoviz --quiet --eval "
db.processed_data.aggregate([
  {\$group: {
    _id: '\$symbol',
    count: {\$sum: 1},
    avg_price: {\$avg: '\$raw_data.close'},
    min_price: {\$min: '\$raw_data.close'},
    max_price: {\$max: '\$raw_data.close'}
  }},
  {\$sort: {_id: 1}}
]).forEach(doc => {
  print('  ' + doc._id.padEnd(12) +
        'Données: ' + doc.count.toString().padStart(4) +
        '  Prix moy: $' + doc.avg_price.toFixed(2).padStart(10) +
        '  Min: $' + doc.min_price.toFixed(2).padStart(10) +
        '  Max: $' + doc.max_price.toFixed(2).padStart(10));
});
"

echo -e "\n============================================================"
echo "  ✅ Visualisation terminée"
echo "============================================================\n"
