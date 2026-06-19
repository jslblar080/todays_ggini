import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import 'thumb_slider.dart';

class LabeledSlider extends StatelessWidget {
  final int value;
  final double min;
  final double max;
  final int divisions;
  final String Function(int) getLabel;
  final ValueChanged<int> onChanged;

  const LabeledSlider({
    super.key,
    required this.value,
    required this.min,
    required this.max,
    required this.divisions,
    required this.getLabel,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final label = getLabel(value);
    return Column(
      children: [
        Row(
          children: [
            Text(
              '${min.toInt()}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Expanded(
              child: ThumbSlider(
                value: value.toDouble(),
                min: min,
                max: max,
                divisions: divisions,
                label: '$value',
                onChanged: (v) => onChanged(v.round()),
              ),
            ),
            Text(
              '${max.toInt()}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
        if (label.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            label,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ],
    );
  }
}