class PreviewBuildInfo {
  const PreviewBuildInfo._();

  static const version = String.fromEnvironment(
    'KEFE_PREVIEW_VERSION',
    defaultValue: 'v9-rc1-local',
  );

  static const commit = String.fromEnvironment(
    'KEFE_PREVIEW_COMMIT',
    defaultValue: 'local',
  );

  static String get shortCommit {
    if (commit == 'local' || commit.length <= 8) return commit;
    return commit.substring(0, 8);
  }

  static String get label => 'Product Preview $version · $shortCommit';
}
