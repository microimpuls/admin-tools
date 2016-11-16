Результаты нагрузочного тестирования (Stress test results)
==========================================================

30000 users online
------------------

Server configuration:
CPU: 2x E5-2650V4 2.2G
Memory: 8x 16GB DDR4-2400 2R*4 ECC REG DIMM
HDD: 2x SEAGATE 2.5", 1TB, SATA3.0 6GB/S

![Grafana](/30kgrafana.png)
![Locust](/30klocust.png)
![After mass messaging](/30kmessage_send.png)

CPU usage on the server during cache initialization (maximum load at cold start) is about 30-40%, after initialization (during continuous working with maximum activity subscribers) about 5%. Thus, this configuration is capable of supporting up to 75000 users online in the normal mode.