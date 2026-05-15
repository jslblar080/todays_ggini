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
    return {
  "user_id": "user_001",
  "request_type": "monthly_plan",
  "selected_style": {
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
    }
  },
  "meta": {
    "period_days": 30,
    "meal_count_per_day": 2,
    "required_meal_count": 60,
    "available_recommendation_count": 75,
    "generated_at": "2026-05-04T17:34:28Z",
    "warnings": []
  },
  "modeling_profile": {
    "goals": [
      "식비 절약",
      "고단백",
      "간편식"
    ],
    "monthly_budget": 300000,
    "period_days": 30,
    "meal_count_per_day": 2,
    "cooking_skill": 2,
    "preferred_categories": [
      "한식",
      "분식"
    ],
    "diversity_level": "낮음",
    "ingredient_preferences": [
      "식물성 단백질류",
      "채소류"
    ],
    "allergy_ingredients": [
      "계란"
    ],
    "budget_period_days": 30,
    "sample_period_days": 3,
    "meal_budget": 5000,
    "weights": {
      "budget": 0.175,
      "nutrition": 0.3,
      "preference": 0.15,
      "difficulty": 0.25,
      "diversity": 0.125
    },
    "max_difficulty": 2,
    "diversity_penalty_strength": 0.2
  },
  "applied_style_adjustment": {
    "applied_style_focus_key": "budget",
    "base_weights": {
      "budget": 0.175,
      "nutrition": 0.3,
      "preference": 0.15,
      "difficulty": 0.25,
      "diversity": 0.125
    },
    "applied_monthly_weights": {
      "budget": 0.312,
      "nutrition": 0.205,
      "preference": 0.098,
      "difficulty": 0.246,
      "diversity": 0.139
    },
    "applied_nutrition_detail_weights": {
      "diet": 0.33,
      "high_protein": 0.34,
      "balance": 0.33
    }
  },
  "monthly_plan": {
    "period_days": 30,
    "meal_count_per_day": 2,
    "required_meal_count": 60,
    "available_recommendation_count": 75,
    "diversity_penalty_strength": 0.2,
    "recent_day_window": 1,
    "warnings": [],
    "summary": {
      "selected_menu_count": 60,
      "unique_menu_count": 55,
      "duplicate_menu_count": 5,
      "total_estimated_cost": 280000,
      "average_daily_cost": 9333,
      "average_calories": 570.2,
      "average_protein": 28.4,
      "average_carbohydrate": 63.1,
      "average_fat": 15.2,
      "average_nutrition_score": 84.3,
      "average_budget_score": 96.7,
      "average_preference_score": 72.5,
      "average_difficulty_score": 79.3,
      "average_diversity_score": 94.1
    },
      "secondary_warnings": [],
      "recommendation_hint": "현재 선택한 스타일이 월간 식단에 안정적으로 반영되었습니다."
    },
    "style_validation": {
      "target_style": "가성비 최우선",
      "status": "pass",
      "message": "월 예산 안에서 여유 있게 식단이 구성되어 가성비 스타일이 잘 반영되었습니다.",
      "checked_metrics": {
        "total_estimated_cost": 280000,
        "monthly_budget": 300000,
        "budget_usage_rate": 0.9333,
        "average_daily_cost": 9333
      },
    "days": [
      {
        "day": 1,
        "meals": [
          {
            "meal_order": 1,
            "selected_menu": {
              "menu_id": "M_138",
              "name": "고단백 치킨 또띠아 랩",
              "category": "양식",
              "final_score": 91.27,
              "base_final_score": 89.27,
              "style_soft_constraint_score": 2,
              "scores": {
                "budget": 100,
                "nutrition": 96.75,
                "preference": 75.0,
                "difficulty": 70,
                "diversity": 100
              },
              "reasons": [
                {
                  "type": "nutrition",
                  "score": 96.75,
                  "level": "매우 적합",
                  "message": "단백질이 30g으로 높아 고단백 목표에 매우 적합합니다."
                }
              ],
              "estimated_cost": 4359,
              "rag_estimated_cost": 4358,
              "pricing_status": "calculated",
              "ingredient_costs": [
                {
                  "ingredient_id": "I_010",
                  "ingredient_name": "닭가슴살",
                  "display_amount": "122g",
                  "amount": 122,
                  "unit": "g",
                  "is_estimated": False,
                  "standard_amount": 1000,
                  "standard_unit_type": "g",
                  "lowest_price": 13900,
                  "lowest_market": "naver_shopping",
                  "delivery_type": "일반배송",
                  "product_title": "닭가슴살 1kg",
                  "purchase_link": "https://example.com/naver/i_010",
                  "estimated_cost": 1696,
                  "pricing_status": "calculated"
                },
                {
                  "ingredient_id": "I_047",
                  "ingredient_name": "또띠아",
                  "display_amount": "70g",
                  "amount": 70,
                  "unit": "g",
                  "is_estimated": False,
                  "standard_amount": 240,
                  "standard_unit_type": "g",
                  "lowest_price": 3900,
                  "lowest_market": "naver_shopping",
                  "delivery_type": "일반배송",
                  "product_title": "또띠아 240g",
                  "purchase_link": "https://example.com/naver/i_047",
                  "estimated_cost": 1138,
                  "pricing_status": "calculated"
                },
                {
                  "ingredient_id": "I_011",
                  "ingredient_name": "양상추",
                  "display_amount": "57g",
                  "amount": 57,
                  "unit": "g",
                  "is_estimated": False,
                  "standard_amount": 300,
                  "standard_unit_type": "g",
                  "lowest_price": 3900,
                  "lowest_market": "naver_shopping",
                  "delivery_type": "일반배송",
                  "product_title": "양상추 300g",
                  "purchase_link": "https://example.com/naver/i_011",
                  "estimated_cost": 741,
                  "pricing_status": "calculated"
                },
                {
                  "ingredient_id": "I_048",
                  "ingredient_name": "토마토",
                  "display_amount": "56g",
                  "amount": 56,
                  "unit": "g",
                  "is_estimated": False,
                  "standard_amount": 500,
                  "standard_unit_type": "g",
                  "lowest_price": 4500,
                  "lowest_market": "naver_shopping",
                  "delivery_type": "일반배송",
                  "product_title": "토마토 500g",
                  "purchase_link": "https://example.com/naver/i_048",
                  "estimated_cost": 504,
                  "pricing_status": "calculated"
                },
                {
                  "ingredient_id": "I_070",
                  "ingredient_name": "소스",
                  "display_amount": "20g",
                  "amount": 20,
                  "unit": "g",
                  "is_estimated": False,
                  "standard_amount": 300,
                  "standard_unit_type": "g",
                  "lowest_price": 4200,
                  "lowest_market": "naver_shopping",
                  "delivery_type": "일반배송",
                  "product_title": "소스 300g",
                  "purchase_link": "https://example.com/naver/i_070",
                  "estimated_cost": 280,
                  "pricing_status": "calculated"
                }
              ],
              "calories": 499,
              "nutrient_summary": {
                "carbohydrate": 51,
                "protein": 30,
                "fat": 15
              },
              "carbohydrate": 51,
              "protein": 30,
              "fat": 15,
              "difficulty": 3,
              "difficulty_detail": {
                "ingredient_count": 5,
                "step_count": 4,
                "cooking_time": 18,
                "estimated_usage_ratio": 0.0,
                "ingredient_points": 1,
                "step_points": 1,
                "cooking_time_points": 1,
                "action_points": 1,
                "estimated_usage_points": 0,
                "difficulty_points": 4
              },
              "ingredients": [
                "닭가슴살",
                "또띠아",
                "양상추",
                "토마토",
                "소스"
              ],
              "ingredient_groups": [
                "육류",
                "곡류",
                "채소류"
              ],
              "ingredient_usages": [
                {
                  "ingredient_id": "I_010",
                  "ingredient_name": "닭가슴살",
                  "display_amount": "122g",
                  "amount": 122,
                  "unit": "g",
                  "is_estimated": False
                },
                {
                  "ingredient_id": "I_047",
                  "ingredient_name": "또띠아",
                  "display_amount": "70g",
                  "amount": 70,
                  "unit": "g",
                  "is_estimated": False
                },
                {
                  "ingredient_id": "I_011",
                  "ingredient_name": "양상추",
                  "display_amount": "57g",
                  "amount": 57,
                  "unit": "g",
                  "is_estimated": False
                },
                {
                  "ingredient_id": "I_048",
                  "ingredient_name": "토마토",
                  "display_amount": "56g",
                  "amount": 56,
                  "unit": "g",
                  "is_estimated": False
                },
                {
                  "ingredient_id": "I_070",
                  "ingredient_name": "소스",
                  "display_amount": "20g",
                  "amount": 20,
                  "unit": "g",
                  "is_estimated": False
                }
              ],
              "similar_menu_ids": [
                "M_138",
                "M_139"
              ],
              "allergy_ingredients": [],
              "recipe": {
                "serving_size": 1,
                "cooking_time": 18,
                "steps": [
                  "닭가슴살 122g을 준비한다.",
                  "재료를 먹기 좋은 크기로 손질한다.",
                  "그릇에 재료를 담고 소스를 곁들인다.",
                  "그릇에 담아 완성한다."
                ],
                "required_ingredients": [
                  "닭가슴살",
                  "또띠아",
                  "양상추",
                  "토마토",
                  "소스"
                ]
              },
              "mmr_score": 31.33
            },
            "alternative_menus": [
              {
                "menu_id": "M_083",
                "name": "구운 닭가슴살 샐러드",
                "category": "샐러드/건강식",
                "final_score": 96.54,
                "base_final_score": 93.54,
                "style_soft_constraint_score": 3,
                "scores": {
                  "budget": 100,
                  "nutrition": 92.0,
                  "preference": 75.0,
                  "difficulty": 100,
                  "diversity": 100
                },
                "reasons": [
                  {
                    "type": "nutrition",
                    "score": 92.0,
                    "level": "매우 적합",
                    "message": "단백질이 36g으로 높아 고단백 목표에 매우 적합합니다."
                  }
                ],
                "estimated_cost": 3682,
                "rag_estimated_cost": 3682,
                "pricing_status": "calculated",
                "ingredient_costs": [
                  {
                    "ingredient_id": "I_010",
                    "ingredient_name": "닭가슴살",
                    "display_amount": "121g",
                    "amount": 121,
                    "unit": "g",
                    "is_estimated": False,
                    "standard_amount": 1000,
                    "standard_unit_type": "g",
                    "lowest_price": 13900,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "닭가슴살 1kg",
                    "purchase_link": "https://example.com/naver/i_010",
                    "estimated_cost": 1682,
                    "pricing_status": "calculated"
                  },
                  {
                    "ingredient_id": "I_011",
                    "ingredient_name": "양상추",
                    "display_amount": "71g",
                    "amount": 71,
                    "unit": "g",
                    "is_estimated": False,
                    "standard_amount": 300,
                    "standard_unit_type": "g",
                    "lowest_price": 3900,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "양상추 300g",
                    "purchase_link": "https://example.com/naver/i_011",
                    "estimated_cost": 923,
                    "pricing_status": "calculated"
                  },
                  {
                    "ingredient_id": "I_012",
                    "ingredient_name": "방울토마토",
                    "display_amount": "55g",
                    "amount": 55,
                    "unit": "g",
                    "is_estimated": False,
                    "standard_amount": 500,
                    "standard_unit_type": "g",
                    "lowest_price": 6900,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "방울토마토 500g",
                    "purchase_link": "https://example.com/naver/i_012",
                    "estimated_cost": 759,
                    "pricing_status": "calculated"
                  },
                  {
                    "ingredient_id": "I_013",
                    "ingredient_name": "오이",
                    "display_amount": "53g",
                    "amount": 53,
                    "unit": "g",
                    "is_estimated": False,
                    "standard_amount": 600,
                    "standard_unit_type": "g",
                    "lowest_price": 3600,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "오이 3개",
                    "purchase_link": "https://example.com/naver/i_013",
                    "estimated_cost": 318,
                    "pricing_status": "calculated"
                  }
                ],
                "calories": 437,
                "nutrient_summary": {
                  "carbohydrate": 26,
                  "protein": 36,
                  "fat": 12
                },
                "carbohydrate": 26,
                "protein": 36,
                "fat": 12,
                "difficulty": 2,
                "difficulty_detail": {
                  "ingredient_count": 4,
                  "step_count": 4,
                  "cooking_time": 16,
                  "estimated_usage_ratio": 0.0,
                  "ingredient_points": 0,
                  "step_points": 1,
                  "cooking_time_points": 1,
                  "action_points": 1,
                  "estimated_usage_points": 0,
                  "difficulty_points": 3
                },
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
                "ingredient_usages": [
                  {
                    "ingredient_id": "I_010",
                    "ingredient_name": "닭가슴살",
                    "display_amount": "121g",
                    "amount": 121,
                    "unit": "g",
                    "is_estimated": False
                  },
                  {
                    "ingredient_id": "I_011",
                    "ingredient_name": "양상추",
                    "display_amount": "71g",
                    "amount": 71,
                    "unit": "g",
                    "is_estimated": False
                  },
                  {
                    "ingredient_id": "I_012",
                    "ingredient_name": "방울토마토",
                    "display_amount": "55g",
                    "amount": 55,
                    "unit": "g",
                    "is_estimated": False
                  },
                  {
                    "ingredient_id": "I_013",
                    "ingredient_name": "오이",
                    "display_amount": "53g",
                    "amount": 53,
                    "unit": "g",
                    "is_estimated": False
                  }
                ],
                "similar_menu_ids": [
                  "M_083",
                  "M_084"
                ],
                "allergy_ingredients": [],
                "recipe": {
                  "serving_size": 1,
                  "cooking_time": 16,
                  "steps": [
                    "닭가슴살 121g을 준비한다.",
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
                "mmr_score": 4.1
              },
              {
                "menu_id": "M_041",
                "name": "간장 두부 비빔밥",
                "category": "한식",
                "final_score": 82.92,
                "base_final_score": 82.92,
                "style_soft_constraint_score": 0,
                "scores": {
                  "budget": 100,
                  "nutrition": 81.5,
                  "preference": 75.0,
                  "difficulty": 70,
                  "diversity": 100
                },
                "reasons": [
                  {
                    "type": "nutrition",
                    "score": 81.5,
                    "level": "적합",
                    "message": "단백질이 22g으로 고단백 목표에 적합한 편입니다."
                  }
                ],
                "estimated_cost": 3937,
                "rag_estimated_cost": 3937,
                "pricing_status": "calculated",
                "ingredient_costs": [
                  {
                    "ingredient_id": "I_001",
                    "ingredient_name": "두부",
                    "display_amount": "150g",
                    "amount": 150,
                    "unit": "g",
                    "is_estimated": False,
                    "standard_amount": 300,
                    "standard_unit_type": "g",
                    "lowest_price": 2300,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "두부 300g",
                    "purchase_link": "https://example.com/naver/i_001",
                    "estimated_cost": 1150,
                    "pricing_status": "calculated"
                  },
                  {
                    "ingredient_id": "I_002",
                    "ingredient_name": "밥",
                    "display_amount": "1공기",
                    "amount": 232,
                    "unit": "g",
                    "is_estimated": True,
                    "standard_amount": 1000,
                    "standard_unit_type": "g",
                    "lowest_price": 8500,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "밥 1kg",
                    "purchase_link": "https://example.com/naver/i_002",
                    "estimated_cost": 1972,
                    "pricing_status": "calculated"
                  },
                  {
                    "ingredient_id": "I_004",
                    "ingredient_name": "상추",
                    "display_amount": "36g",
                    "amount": 36,
                    "unit": "g",
                    "is_estimated": False,
                    "standard_amount": 200,
                    "standard_unit_type": "g",
                    "lowest_price": 2600,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "상추 200g",
                    "purchase_link": "https://example.com/naver/i_004",
                    "estimated_cost": 468,
                    "pricing_status": "calculated"
                  },
                  {
                    "ingredient_id": "I_005",
                    "ingredient_name": "당근",
                    "display_amount": "46g",
                    "amount": 46,
                    "unit": "g",
                    "is_estimated": False,
                    "standard_amount": 500,
                    "standard_unit_type": "g",
                    "lowest_price": 2500,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "당근 500g",
                    "purchase_link": "https://example.com/naver/i_005",
                    "estimated_cost": 230,
                    "pricing_status": "calculated"
                  },
                  {
                    "ingredient_id": "I_003",
                    "ingredient_name": "고추장",
                    "display_amount": "13g",
                    "amount": 13,
                    "unit": "g",
                    "is_estimated": False,
                    "standard_amount": 500,
                    "standard_unit_type": "g",
                    "lowest_price": 4500,
                    "lowest_market": "naver_shopping",
                    "delivery_type": "일반배송",
                    "product_title": "고추장 500g",
                    "purchase_link": "https://example.com/naver/i_003",
                    "estimated_cost": 117,
                    "pricing_status": "calculated"
                  }
                ],
                "calories": 544,
                "nutrient_summary": {
                  "carbohydrate": 67,
                  "protein": 22,
                  "fat": 13
                },
                "carbohydrate": 67,
                "protein": 22,
                "fat": 13,
                "difficulty": 3,
                "difficulty_detail": {
                  "ingredient_count": 5,
                  "step_count": 4,
                  "cooking_time": 18,
                  "estimated_usage_ratio": 0.2,
                  "ingredient_points": 1,
                  "step_points": 1,
                  "cooking_time_points": 1,
                  "action_points": 1,
                  "estimated_usage_points": 0,
                  "difficulty_points": 4
                },
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
                "ingredient_usages": [
                  {
                    "ingredient_id": "I_001",
                    "ingredient_name": "두부",
                    "display_amount": "150g",
                    "amount": 150,
                    "unit": "g",
                    "is_estimated": False
                  },
                  {
                    "ingredient_id": "I_002",
                    "ingredient_name": "밥",
                    "display_amount": "1공기",
                    "amount": 232,
                    "unit": "g",
                    "is_estimated": True
                  },
                  {
                    "ingredient_id": "I_004",
                    "ingredient_name": "상추",
                    "display_amount": "36g",
                    "amount": 36,
                    "unit": "g",
                    "is_estimated": False
                  },
                  {
                    "ingredient_id": "I_005",
                    "ingredient_name": "당근",
                    "display_amount": "46g",
                    "amount": 46,
                    "unit": "g",
                    "is_estimated": False
                  },
                  {
                    "ingredient_id": "I_003",
                    "ingredient_name": "고추장",
                    "display_amount": "13g",
                    "amount": 13,
                    "unit": "g",
                    "is_estimated": False
                  }
                ],
                "similar_menu_ids": [
                  "M_041",
                  "M_042"
                ],
                "allergy_ingredients": [],
                "recipe": {
                  "serving_size": 1,
                  "cooking_time": 18,
                  "steps": [
                    "두부 150g을 준비한다.",
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
                "mmr_score": 0.61
              }
            ]
          }
        ],
        "total_estimated_cost": 12466,
        "total_calories": 2060
      }
    ],
    "style_validation": {
      "target_style": "고단백 관리식",
      "status": "warning",
      "message": "고단백 스타일에 맞게 평균 단백질이 충분히 높게 구성되었습니다. 다만 동일 메뉴 반복 비율이 높아 월간 식단 다양성 보완이 필요합니다.",
      "checked_metrics": {
        "average_protein": 34.64,
        "recommended_minimum_protein": 28
      },
      "secondary_warnings": [
        {
          "type": "duplicate_menu",
          "level": "info",
          "message": "월간 식단 내 동일 menu_id가 일부 반복되었습니다.",
          "value": 33
        }
      ],
      "recommendation_hint": "고단백 스타일에서는 단백질 25g 이상 메뉴를 우선 배치하거나, protein 기준 soft constraint를 강화할 수 있습니다."
    }
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