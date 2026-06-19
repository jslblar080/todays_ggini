import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class SocialButton extends StatelessWidget {
  final String label;
  final Color color;
  final Color labelColor;
  final VoidCallback onTap;
  final bool border;
  final String? imagePath;

  const SocialButton({
    super.key,
    required this.label,
    required this.color,
    required this.onTap,
    this.labelColor = Colors.black,
    this.border = false,
    this.imagePath,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 64,
        height: 64,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 4,
            ),
          ],
        ),
        child: ClipOval(
          child: imagePath != null
              ? Image.asset(
                  imagePath!,
                  width: 60,
                  height: 60,
                  fit: BoxFit.cover,
                )
              : Container(
                  color: color,
                  child: Center(
                    child: Text(
                      label,
                      style: TextStyle(color: labelColor),
                    ),
                  ),
                ),
        ),
      ),
    );
  }
}