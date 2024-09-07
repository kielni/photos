# export photos from Apple Photos

Export photos from Apple Photo to filesystem. Review, then upload to S3
and sync with Ente for sharing outside of Apple jail.

`python apple/main.py ~/Pictures/staging`

  - copy favorited photos and live photos from the last 45 days to staging directory
  - re-encode mov to mp4

`python apple/main.py ~/Pictures/staging --sync`
    
      - copy photos to S3 bucket
      - update Ente database with new photos


    
