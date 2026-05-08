// 项目类型常量 —— 全局唯一来源
// 后端 Project.category 字段无字典表约束，前端所有创建/筛选/统计入口必须从这里 import
// 修改这里需同步检查：ProjectList.vue / ProjectForm.vue / StatisticsView.vue / AiFloatWidget.vue

export const PROJECT_CATEGORIES = [
  '环保',
  '支教',
  '社区帮扶',
  '赛事服务',
  '医疗健康',
  '科技推广',
  '文化宣传',
  '其他',
] as const

export type ProjectCategory = typeof PROJECT_CATEGORIES[number]
