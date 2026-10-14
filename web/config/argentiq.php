<?php

return [
    'python' => env('ARGENTIQ_PYTHON', 'python'),
    'java' => env('ARGENTIQ_JAVA', 'java'),
    'database' => env('ARGENTIQ_MARKET_DB', dirname(base_path()).DIRECTORY_SEPARATOR.'argentiq.sqlite3'),
    'food_database' => env('ARGENTIQ_FOOD_DB', dirname(base_path()).DIRECTORY_SEPARATOR.'food_history.sqlite3'),
];
