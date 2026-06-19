class MealStyle {
  final String styleId;
  final String styleName;
  final List<String> representativeMenus;
  final Map<String, int> displayScores;
  final Map<String, String> displayLabels;
  final String summaryComment;

  const MealStyle({
    required this.styleId,
    required this.styleName,
    required this.representativeMenus,
    required this.displayScores,
    required this.displayLabels,
    required this.summaryComment,
  });

  factory MealStyle.fromJson(Map<String, dynamic> json) {
  return MealStyle(
    styleId: json['style_id'] as String,
    styleName: json['style_name'] as String,
    representativeMenus: List<String>.from(json['representative_menus'] as List),
    displayScores: Map<String, int>.from(json['display_scores'] as Map),
    displayLabels: Map<String, String>.from(json['display_labels'] as Map),
    summaryComment: json['summary_comment'] as String,
  );
}
}