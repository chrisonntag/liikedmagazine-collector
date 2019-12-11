# Quality Model Checker

### Crontab

```
# Wochentags (80x pro Tag)
4,6,7,10-12,31,46,47,53 7,8,10,13,15,18,21,22 * * 1-5 python /home/user/scrape

# Samstag (119x)
1-4,6-9,13-15,27,28,42-45 11-13,16,17,22,23 * * 6 python /home/user/scrape

# Sonntag (178x)
9-22,27-48 10 * * 0 python /home/user/scrape
0-10,12-32 11 * * 0 python /home/user/scrape
2-14,34-42 13-16,22 * * 0 python /home/user/scrape
```