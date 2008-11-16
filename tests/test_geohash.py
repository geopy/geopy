from geopy.geohash import Geohash


class TestWhenConvertingKnownGeohashValues:
    # These known-good hashes were taken from geohash.org on 16 November 2008.
    all_four_quadrants = [
        ('41.4997130', '-81.6937160', 'dpmuj4b3q7nq8'), # Cleveland
        ('19.0176560', '72.8561780', 'te7u1yh1zupbc'), # Mumbai
        ('-31.9554000', '115.8585900', 'qd66hqtwkcdjy'), # Perth
        ('-34.6117810', '-58.4173090', '69y7nejgf03k0'), # Buenos Aires
    ]
    edge_cases = [
        ('-90', '0', 'h000'),
        ('90', '0', 'upbp'),
        ('0', '-180', '800000000'),
        ('0', '180', 'xbpbpbpbp'),
    ]
    known_hashes = all_four_quadrants + edge_cases

    def point_returns_geohash(self, latitude, longitude, expected_hash):
        geohash_length = len(expected_hash)
        hasher = Geohash(precision=geohash_length)
        geohash = hasher.encode(latitude, longitude)
        assert geohash == expected_hash

    def test_should_convert_points_to_hashes(self):
        for latitude, longitude, geohash in self.known_hashes:
            yield self.point_returns_geohash, latitude, longitude, geohash

    def test_should_provide_requested_precision(self):
        latitude, longitude, full_geohash = self.known_hashes[0]
        for precision in range(0, 14):
            geohash = full_geohash[:precision]
            yield self.point_returns_geohash, latitude, longitude, geohash

