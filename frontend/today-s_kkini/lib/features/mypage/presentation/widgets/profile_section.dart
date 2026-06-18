import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:typed_data';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../core/widgets/popup.dart';

class ProfileSection extends StatefulWidget {
  final String? name;
  final String? imageUrl;
  final String persona;
  final Future<String> Function(String)? onNameChanged;
  final Future<String> Function(Uint8List, String)? onImageChanged;

  const ProfileSection({
    super.key,
    this.name,
    this.imageUrl,
    this.persona = '자취생',
    this.onNameChanged,
    this.onImageChanged,
  });

  @override
  State<ProfileSection> createState() => _ProfileSectionState();
}

class _ProfileSectionState extends State<ProfileSection> {
  late String _displayName;
  String? _imageUrl;
  Uint8List? _imageBytes;

  @override
  void initState() {
    super.initState();
    _displayName = widget.name ?? '${widget.persona}_1';
    _imageUrl = widget.imageUrl;
  }

  @override
  void didUpdateWidget(covariant ProfileSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.imageUrl != widget.imageUrl) {
      _imageUrl = widget.imageUrl;
      _imageBytes = null;  // 서버에서 새 URL 받았으면 로컬 바이트 초기화
    }
    if (oldWidget.name != widget.name) {
      _displayName = widget.name ?? '${widget.persona}_1';
    }
  }

  void _showEditNameDialog() {
    final controller = TextEditingController(text: _displayName);
    showAppPopupWidget(
      context: context,
      title: '[닉네임 변경]',
      contentWidget: TextField(
        controller: controller,
        maxLength: 15,
        style: Theme.of(context).textTheme.bodyMedium,
        decoration: InputDecoration(
          hintText: '새 닉네임을 입력하세요',
          hintStyle: Theme.of(context).textTheme.bodyMedium,
          counterStyle: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: AppColors.textSecondary,
          ),
          enabledBorder: UnderlineInputBorder(
            borderSide: BorderSide(color: AppColors.border),
          ),
          focusedBorder: UnderlineInputBorder(
            borderSide: BorderSide(color: AppColors.primary),
          ),
        ),
      ),
      leftButtonText: '취소',
      rightButtonText: '확인',
      leftButtonColor: AppColors.textSecondary,
      rightButtonColor: AppColors.primary,
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () async {
        final newName = controller.text.trim();
        if (newName.isNotEmpty) {
          if (widget.onNameChanged != null) {
            try {
              final savedName = await widget.onNameChanged!(newName);
              setState(() => _displayName = savedName);
            } catch (e) {
              setState(() => _displayName = newName);
            }
          } else {
            setState(() => _displayName = newName);
          }
        }
        if (context.mounted) Navigator.pop(context);
      },
    );
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked != null) {
      final bytes = await picked.readAsBytes();
      setState(() => _imageBytes = bytes);

      if (widget.onImageChanged != null) {
        try {
          final url = await widget.onImageChanged!(bytes, picked.name);
          setState(() => _imageUrl = url);
        } catch (e) {
          // 업로드 실패해도 로컬 미리보기 유지
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: AppColors.primaryLight,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          GestureDetector(
            onTap: _pickImage,
            child: Stack(
              children: [
                CircleAvatar(
                  radius: 40,
                  backgroundColor: Colors.white,
                  child: ClipOval(
                    child: _imageBytes != null
                        ? Image.memory(
                            _imageBytes!,
                            width: 80,
                            height: 80,
                            fit: BoxFit.cover,
                          )
                        : _imageUrl != null
                            ? Image.network(
                                _imageUrl!,
                                width: 80,
                                height: 80,
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => Image.asset(
                                  'assets/images/pic.png',
                                  width: 80,
                                  height: 80,
                                  fit: BoxFit.cover,
                                ),
                              )
                            : Image.asset(
                                'assets/images/pic.png',
                                width: 80,
                                height: 80,
                                fit: BoxFit.cover,
                              ),
                  ),
                ),
                Positioned(
                  bottom: 0,
                  right: 0,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: const BoxDecoration(
                      color: AppColors.primary,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.camera_alt, size: 16, color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              GestureDetector(
                onTap: _showEditNameDialog,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _displayName,
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(width: 4),
                    const Icon(Icons.edit, size: 18, color: AppColors.textSecondary),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}