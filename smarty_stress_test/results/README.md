Результаты нагрузочного тестирования Smarty (Stress test results)
=================================================================

30k users online
----------------

30000 users online stress test.

Server configuration:

```
CPU: 2x E5-2650V4 2.2G
Memory: 8x 16GB DDR4-2400 2R*4 ECC REG DIMM
HDD: 2x SEAGATE 2.5", 1TB, SATA3.0 6GB/S
Database: Oracle (1 instance, external server)
```

CPU usage on the Smarty server during cache initialization (maximum load at cold start) is about 30-40%, after initialization (during continuous working with maximum subscribers activity) about 5%. Thus, this configuration is capable of supporting up to 75000 users online in the normal mode and 100000 users online in high load mode.

![Grafana](/smarty_stress_test/results/30kgrafana.png)
![Locust](/smarty_stress_test/results/30klocust.png)
![After mass messaging](/smarty_stress_test/results/30kmessage_send.png)

100k users online
-----------------

100000 users online stress test.

Server config is the same.

![Grafana](/smarty_stress_test/results/100k_grafana_part1.png)
![Grafana](/smarty_stress_test/results/100k_grafana_part2.png)
![Locust](/smarty_stress_test/results/100k_locust.png)
![Locust](/smarty_stress_test/results/100k_locust_htop.png)
![Grafana](/smarty_stress_test/results/100k_grafana_part3.png)
![Grafana](/smarty_stress_test/results/100k_grafana_part4.png)

CPU usage on the Smarty server during cache initialization (maximum load at cold start) is about 90%, after initialization is about 40% and during continuous working with usual subscribers activity is about 20%.