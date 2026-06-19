import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../../core/theme/app_colors.dart';

class ImageThumbShape extends SliderComponentShape {
  final ui.Image? image;
  final bool showLabel;

  ImageThumbShape({this.image, this.showLabel = true});

  @override
  Size getPreferredSize(bool isEnabled, bool isDiscrete) {
    return const Size(40, 40);
  }

  @override
  void paint(
    PaintingContext context,
    Offset center, {
    required Animation<double> activationAnimation,
    required Animation<double> enableAnimation,
    required bool isDiscrete,
    required TextPainter labelPainter,
    required RenderBox parentBox,
    required SliderThemeData sliderTheme,
    required ui.TextDirection textDirection,
    required double value,
    required double textScaleFactor,
    required Size sizeWithOverflow,
  }) {
    final canvas = context.canvas;

    if (image != null) {
      final thumbHeight = 40.0;
      final scale = thumbHeight / image!.height;
      final thumbWidth = image!.width * scale;
      final src = Rect.fromLTWH(0, 0, image!.width.toDouble(), image!.height.toDouble());
      final dst = Rect.fromCenter(center: center, width: thumbWidth, height: thumbHeight);
      canvas.drawImageRect(image!, src, dst, Paint());
    } else {
      final paint = Paint()..color = AppColors.primary;
      canvas.drawCircle(center, 18, paint);
    }

    if (showLabel) {
      final tp = TextPainter(
        text: TextSpan(
          text: labelPainter.text?.toPlainText() ?? '',
          style: const TextStyle(
            fontSize: 16,
            color: Colors.white,
          ),
        ),
        textDirection: ui.TextDirection.ltr,
      )..layout();

      tp.paint(
        canvas,
        Offset(
          center.dx - tp.width / 2,
          center.dy - tp.height / 2,
        ),
      );
    }
  }
}

class ThumbSlider extends StatefulWidget {
  final double value;
  final double min;
  final double max;
  final int divisions;
  final String? label;
  final ValueChanged<double> onChanged;
  final bool showThumbLabel;

  const ThumbSlider({
    super.key,
    required this.value,
    required this.min,
    required this.max,
    required this.divisions,
    this.label,
    required this.onChanged,
    this.showThumbLabel = true,
  });

  @override
  State<ThumbSlider> createState() => _ThumbSliderState();
}

class _ThumbSliderState extends State<ThumbSlider> {
  ui.Image? _thumbImage;

  @override
  void initState() {
    super.initState();
    _loadImage();
  }

  Future<void> _loadImage() async {
    final data = await rootBundle.load('assets/images/slider.png');
    final codec = await ui.instantiateImageCodec(
      data.buffer.asUint8List(),
    );
    final frame = await codec.getNextFrame();
    if (mounted) {
      setState(() => _thumbImage = frame.image);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SliderTheme(
      data: SliderTheme.of(context).copyWith(
        activeTrackColor: AppColors.primary,
        inactiveTrackColor: AppColors.border,
        trackHeight: 6,
        thumbShape: ImageThumbShape(
          image: _thumbImage,
          showLabel: widget.showThumbLabel,
        ),
        overlayShape: SliderComponentShape.noOverlay,
        showValueIndicator: ShowValueIndicator.always,
        valueIndicatorTextStyle: const TextStyle(
          color: Colors.white,
          fontSize: 14,
        ),
      ),
      child: Slider(
        value: widget.value,
        min: widget.min,
        max: widget.max,
        divisions: widget.divisions,
        label: widget.label,
        onChanged: widget.onChanged,
      ),
    );
  }
}