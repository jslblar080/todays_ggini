def get_mock_3days_response():
    """3일치 식단 샘플 Mock 데이터 반환"""
    return  {
                "status": "success",
                "message": "AI 모델링 연동 전 임시 응답입니다.",
                "data": {
        "user_id": "user_006",
        "request_type": "meal_style_candidates",
        "meta": {
            "sample_period_days": 3,
            "meal_count_per_day": 1,
            "total_style_count": 3,
            "generated_at": "2026-05-12T02:52:37Z",
            "warnings": []
        },
        "meal_style_candidates": [
            {
            "style_id": "budget_first",
            "style_name": "가성비 최우선",
            "description": "예산을 가장 우선으로 고려한 식단",
            "summary_comment": "예산 부담을 줄이고 간편하게 구성한 식단입니다.",
            "source_goal": "식비 절약",
            "focus_key": "budget",
            "display_scores": {
                "health": 7,
                "cost_efficiency": 10,
                "taste": 8,
                "cooking_ease": 7
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리"
            },
            "sample_plan": {
                "period_days": 3,
                "meal_count_per_day": 1,
                "days": [
                {
                    "day": 1,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_001",
                        "name": "두부 비빔밥",
                        "category": "한식",
                        "estimated_cost": 3536,
                        "calories": 600,
                        "protein": 25
                    }
                    ]
                },
                {
                    "day": 2,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_006",
                        "name": "된장찌개 정식",
                        "category": "한식",
                        "estimated_cost": 3484,
                        "calories": 679,
                        "protein": 24
                    }
                    ]
                },
                {
                    "day": 3,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_003",
                        "name": "닭가슴살 샐러드",
                        "category": "샐러드/건강식",
                        "estimated_cost": 3556,
                        "calories": 397,
                        "protein": 33
                    }
                    ]
                }
                ]
            }
            },
            {
            "style_id": "nutrition_balance",
            "style_name": "영양 균형식",
            "description": "칼로리와 단백질 균형을 함께 고려한 식단",
            "summary_comment": "영양 균형을 고려해 건강하게 구성한 식단입니다.",
            "source_goal": "영양 균형",
            "focus_key": "nutrition",
            "display_scores": {
                "health": 8,
                "cost_efficiency": 10,
                "taste": 6,
                "cooking_ease": 7
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리"
            },
            "sample_plan": {
                "period_days": 3,
                "meal_count_per_day": 1,
                "days": [
                {
                    "day": 1,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_008",
                        "name": "닭가슴살 포케",
                        "category": "샐러드/건강식",
                        "estimated_cost": 5310,
                        "calories": 476,
                        "protein": 35
                    }
                    ]
                },
                {
                    "day": 2,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_009",
                        "name": "토마토 파스타",
                        "category": "양식",
                        "estimated_cost": 2086,
                        "calories": 701,
                        "protein": 17
                    }
                    ]
                },
                {
                    "day": 3,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_001",
                        "name": "두부 비빔밥",
                        "category": "한식",
                        "estimated_cost": 3536,
                        "calories": 600,
                        "protein": 25
                    }
                    ]
                }
                ]
            }
            },
            {
            "style_id": "diet_light",
            "style_name": "가벼운 관리식",
            "description": "칼로리 부담을 줄이고 가볍게 구성한 식단",
            "summary_comment": "부담이 적은 메뉴를 중심으로 구성한 식단입니다.",
            "source_goal": "다이어트",
            "focus_key": "nutrition",
            "display_scores": {
                "health": 8,
                "cost_efficiency": 10,
                "taste": 8,
                "cooking_ease": 7
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리"
            },
            "sample_plan": {
                "period_days": 3,
                "meal_count_per_day": 1,
                "days": [
                {
                    "day": 1,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_001",
                        "name": "두부 비빔밥",
                        "category": "한식",
                        "estimated_cost": 3536,
                        "calories": 600,
                        "protein": 25
                    }
                    ]
                },
                {
                    "day": 2,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_006",
                        "name": "된장찌개 정식",
                        "category": "한식",
                        "estimated_cost": 3484,
                        "calories": 679,
                        "protein": 24
                    }
                    ]
                },
                {
                    "day": 3,
                    "meals": [
                    {
                        "meal_order": 1,
                        "menu_id": "M_003",
                        "name": "닭가슴살 샐러드",
                        "category": "샐러드/건강식",
                        "estimated_cost": 3556,
                        "calories": 397,
                        "protein": 33
                    }
                    ]
                }
                ]
            }
            }
        ]
        }
    }

def get_mock_month_data_response():
    """한 달치 식단 샘플 Mock 데이터 반환"""
    return  {
            "user_id": "user_001",
            "request_type": "monthly_plan",
            "selected_style_id": "budget_first",
            "meta": {
                
                # 월간 식단 생성 기간
                "period_days": 30,    # int
                "meal_count_per_day": 2,
                "required_meal_count": 60,
                "available_recommendation_count": 75,
                "generated_at": "2026-05-04T17:34:28Z",
                "warnings": []
            },
            "monthly_plan": {
                "period_days": 30,
                "meal_count_per_day": 1,
                "required_meal_count": 30,
                "available_recommendation_count": 6,
                "diversity_penalty_strength": 0.2,
                "recent_day_window": 1,
                "warnings": [
                "요청한 30개 식단 중 조건을 통과한 추천 메뉴가 6개입니다. 후보가 부족한 경우 일부 메뉴가 반복 배치될 수 있습니다."
                ],
                "days": [
                {
                    "day": 1,
                    "meals": [
                    {
                        "meal_order": 1,
                        "selected_menu": {
                        "menu_id": "M_001",
                        "name": "두부 비빔밥",
                        "category": "한식",
                        "final_score": 87.49,
                        "estimated_cost": 3536,
                        "calories": 600,
                        "protein": 25,
                        "ingredients": [
                            "두부",
                            "밥",
                            "상추",
                            "당근",
                            "고추장"
                        ],
                        "ingredient_groups": [
                            "식물성 단백질류",
                            "곡류",
                            "채소류"
                        ],
                        "recipe": {
                            "serving_size": 1,
                            "cooking_time": 18,
                            "steps": [
                            "두부 156g을 준비한다.",
                            "재료를 먹기 좋은 크기로 손질한다.",
                            "그릇에 재료를 담고 소스를 곁들인다.",
                            "그릇에 담아 완성한다."
                            ],
                            "required_ingredients": [
                            "두부",
                            "밥",
                            "상추",
                            "당근",
                            "고추장"
                            ]
                        },
                        "scores": {
                            "budget": 100,
                            "nutrition": 70,
                            "preference": 100.0,
                            "difficulty": 70,
                            "diversity": 100
                        },
                        "reasons": [
                            {
                            "type": "budget",
                            "score": 100,
                            "level": "매우 적합",
                            "message": "한 끼 예산 6,000원보다 2,464원 저렴해 예산 여유가 큰 메뉴입니다."
                            },
                            {
                            "type": "nutrition",
                            "score": 70,
                            "level": "보통",
                            "message": "선택한 목표에서 영양 기준은 보조적으로 반영되었습니다."
                            },
                            {
                            "type": "preference",
                            "score": 100.0,
                            "level": "매우 적합",
                            "message": "선호 카테고리 '한식'에 해당하고, 선호 재료군(식물성 단백질류, 채소류)도 포함되어 있습니다."
                            },
                            {
                            "type": "difficulty",
                            "score": 70,
                            "level": "보통",
                            "message": "메뉴 난이도 3로 사용자 가능 난이도보다 1단계 높아 약간의 조리 부담이 있을 수 있습니다."
                            },
                            {
                            "type": "diversity",
                            "score": 100,
                            "level": "매우 적합",
                            "message": "최근 선택된 메뉴와 유사도가 낮아 반복을 줄일 수 있습니다."
                            }
                        ]
                        },
                        "alternative_menus": [
                        {
                            "menu_id": "M_006",
                            "name": "된장찌개 정식",
                            "category": "한식",
                            "final_score": 87.49,
                            "estimated_cost": 3484,
                            "calories": 679,
                            "protein": 24,
                            "ingredients": [
                            "된장",
                            "두부",
                            "애호박",
                            "양파",
                            "밥"
                            ],
                            "ingredient_groups": [
                            "식물성 단백질류",
                            "채소류",
                            "곡류"
                            ],
                            "recipe": {
                            "serving_size": 1,
                            "cooking_time": 23,
                            "steps": [
                                "된장 28g을 준비한다.",
                                "재료를 먹기 좋은 크기로 손질한다.",
                                "냄비에 육수와 재료를 넣고 끓인다.",
                                "그릇에 담아 완성한다."
                            ],
                            "required_ingredients": [
                                "된장",
                                "두부",
                                "애호박",
                                "양파",
                                "밥"
                            ]
                            },
                            "scores": {
                            "budget": 100,
                            "nutrition": 70,
                            "preference": 100.0,
                            "difficulty": 70,
                            "diversity": 100
                            },
                            "reasons": [
                            {
                                "type": "budget",
                                "score": 100,
                                "level": "매우 적합",
                                "message": "한 끼 예산 6,000원보다 2,516원 저렴해 예산 여유가 큰 메뉴입니다."
                            },
                            {
                                "type": "nutrition",
                                "score": 70,
                                "level": "보통",
                                "message": "선택한 목표에서 영양 기준은 보조적으로 반영되었습니다."
                            },
                            {
                                "type": "preference",
                                "score": 100.0,
                                "level": "매우 적합",
                                "message": "선호 카테고리 '한식'에 해당하고, 선호 재료군(식물성 단백질류, 채소류)도 포함되어 있습니다."
                            },
                            {
                                "type": "difficulty",
                                "score": 70,
                                "level": "보통",
                                "message": "메뉴 난이도 3로 사용자 가능 난이도보다 1단계 높아 약간의 조리 부담이 있을 수 있습니다."
                            },
                            {
                                "type": "diversity",
                                "score": 100,
                                "level": "매우 적합",
                                "message": "최근 선택된 메뉴와 유사도가 낮아 반복을 줄일 수 있습니다."
                            }
                            ]
                        },
                        {
                            "menu_id": "M_003",
                            "name": "닭가슴살 샐러드",
                            "category": "샐러드/건강식",
                            "final_score": 80.62,
                            "estimated_cost": 3556,
                            "calories": 397,
                            "protein": 33,
                            "ingredients": [
                            "닭가슴살",
                            "양상추",
                            "방울토마토",
                            "오이"
                            ],
                            "ingredient_groups": [
                            "육류",
                            "채소류"
                            ],
                            "recipe": {
                            "serving_size": 1,
                            "cooking_time": 16,
                            "steps": [
                                "닭가슴살 103g을 준비한다.",
                                "재료를 먹기 좋은 크기로 손질한다.",
                                "그릇에 재료를 담고 소스를 곁들인다.",
                                "그릇에 담아 완성한다."
                            ],
                            "required_ingredients": [
                                "닭가슴살",
                                "양상추",
                                "방울토마토",
                                "오이"
                            ]
                            },
                            "scores": {
                            "budget": 100,
                            "nutrition": 70,
                            "preference": 45.0,
                            "difficulty": 70,
                            "diversity": 100
                            },
                            "reasons": [
                            {
                                "type": "budget",
                                "score": 100,
                                "level": "매우 적합",
                                "message": "한 끼 예산 6,000원보다 2,444원 저렴해 예산 여유가 큰 메뉴입니다."
                            },
                            {
                                "type": "nutrition",
                                "score": 70,
                                "level": "보통",
                                "message": "선택한 목표에서 영양 기준은 보조적으로 반영되었습니다."
                            },
                            {
                                "type": "preference",
                                "score": 45.0,
                                "level": "낮음",
                                "message": "선호 카테고리나 선호 재료군과의 일치도가 낮아 취향 반영이 약한 편입니다."
                            },
                            {
                                "type": "difficulty",
                                "score": 70,
                                "level": "보통",
                                "message": "메뉴 난이도 3로 사용자 가능 난이도보다 1단계 높아 약간의 조리 부담이 있을 수 있습니다."
                            },
                            {
                                "type": "diversity",
                                "score": 100,
                                "level": "매우 적합",
                                "message": "최근 선택된 메뉴와 유사도가 낮아 반복을 줄일 수 있습니다."
                            }
                            ]
                        }
                        ]
                    }
                    ],
                    "total_estimated_cost": 3536,
                    "total_calories": 600
                }
            ]
        }
    }

def get_mock_3days_data_front_response(user_id, sample_period_days):
    return {
  "user_id": user_id,
  "request_type": "meal_style_candidates",
  "meta": {
    "sample_period_days": sample_period_days,
    "meal_count_per_day": 1,
    "total_style_count": 3,
    "generated_at": "2026-05-12T02:52:37Z",
    "warnings": []
  },
  "meal_style_candidates": [
    {
      "style_id": "budget_first",
      "style_name": "가성비 최우선",
      "description": "예산을 가장 우선으로 고려한 식단",
      "summary_comment": "예산 부담을 줄이고 간편하게 구성한 식단입니다.",
      "source_goal": "식비 절약",
      "focus_key": "budget",
      "display_scores": {
        "health": 7,
        "cost_efficiency": 10,
        "taste": 8,
        "cooking_ease": 7
      },
      "display_labels": {
        "health": "건강",
        "cost_efficiency": "가성비",
        "taste": "맛",
        "cooking_ease": "조리"
      },
      "sample_plan": {
        "period_days": 3,
        "meal_count_per_day": 1,
        "days": [
          {
            "day": 1,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_001",
                "name": "두부 비빔밥",
                "category": "한식",
                "estimated_cost": 3536,
                "calories": 600,
                "protein": 25
              }
            ]
          },
          {
            "day": 2,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_006",
                "name": "된장찌개 정식",
                "category": "한식",
                "estimated_cost": 3484,
                "calories": 679,
                "protein": 24
              }
            ]
          },
          {
            "day": 3,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_003",
                "name": "닭가슴살 샐러드",
                "category": "샐러드/건강식",
                "estimated_cost": 3556,
                "calories": 397,
                "protein": 33
              }
            ]
          }
        ]
      }
    },
    {
      "style_id": "nutrition_balance",
      "style_name": "영양 균형식",
      "description": "칼로리와 단백질 균형을 함께 고려한 식단",
      "summary_comment": "영양 균형을 고려해 건강하게 구성한 식단입니다.",
      "source_goal": "영양 균형",
      "focus_key": "nutrition",
      "display_scores": {
        "health": 8,
        "cost_efficiency": 10,
        "taste": 6,
        "cooking_ease": 7
      },
      "display_labels": {
        "health": "건강",
        "cost_efficiency": "가성비",
        "taste": "맛",
        "cooking_ease": "조리"
      },
      "sample_plan": {
        "period_days": 3,
        "meal_count_per_day": 1,
        "days": [
          {
            "day": 1,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_008",
                "name": "닭가슴살 포케",
                "category": "샐러드/건강식",
                "estimated_cost": 5310,
                "calories": 476,
                "protein": 35
              }
            ]
          },
          {
            "day": 2,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_009",
                "name": "토마토 파스타",
                "category": "양식",
                "estimated_cost": 2086,
                "calories": 701,
                "protein": 17
              }
            ]
          },
          {
            "day": 3,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_001",
                "name": "두부 비빔밥",
                "category": "한식",
                "estimated_cost": 3536,
                "calories": 600,
                "protein": 25
              }
            ]
          }
        ]
      }
    },
    {
      "style_id": "diet_light",
      "style_name": "가벼운 관리식",
      "description": "칼로리 부담을 줄이고 가볍게 구성한 식단",
      "summary_comment": "부담이 적은 메뉴를 중심으로 구성한 식단입니다.",
      "source_goal": "다이어트",
      "focus_key": "nutrition",
      "display_scores": {
        "health": 8,
        "cost_efficiency": 10,
        "taste": 8,
        "cooking_ease": 7
      },
      "display_labels": {
        "health": "건강",
        "cost_efficiency": "가성비",
        "taste": "맛",
        "cooking_ease": "조리"
      },
      "sample_plan": {
        "period_days": 3,
        "meal_count_per_day": 1,
        "days": [
          {
            "day": 1,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_001",
                "name": "두부 비빔밥",
                "category": "한식",
                "estimated_cost": 3536,
                "calories": 600,
                "protein": 25
              }
            ]
          },
          {
            "day": 2,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_006",
                "name": "된장찌개 정식",
                "category": "한식",
                "estimated_cost": 3484,
                "calories": 679,
                "protein": 24
              }
            ]
          },
          {
            "day": 3,
            "meals": [
              {
                "meal_order": 1,
                "menu_id": "M_003",
                "name": "닭가슴살 샐러드",
                "category": "샐러드/건강식",
                "estimated_cost": 3556,
                "calories": 397,
                "protein": 33
              }
            ]
          }
        ]
      }
    }
  ]
}